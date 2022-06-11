#!/usr/bin/env python3

import os
import sys
import time
from pathlib import Path

from broker import cfg
from broker._utils import _log
from broker._utils._log import _console_clear
from broker._utils.tools import _date, log, print_tb
from broker._utils.yaml import Yaml
from broker.errors import QuietExit
from broker.lib import state

# from broker.test_setup.user_set import providers

Ebb = cfg.Ebb
watch_only_jobs = True


def get_eth_address_from_cfg():
    hidden_base_dir = Path.home() / ".ebloc-broker"
    fn = hidden_base_dir / "cfg.yaml"
    if not os.path.isfile(fn):
        if not os.path.isdir(hidden_base_dir):
            raise QuietExit(f"E: {hidden_base_dir} is not initialized")

        raise QuietExit(f"E: {fn} is not created")

    cfg_yaml = Yaml(fn)
    cfg = cfg_yaml["cfg"]
    return cfg.w3.toChecksumAddress(cfg["eth_address"].lower())


def watch(eth_address="", from_block=None):
    from_block = 15394725
    if not eth_address:
        try:
            eth_address = get_eth_address_from_cfg()
        except Exception as e:
            log(f"E: {e}\neth_address is empty, run as: ./watch.py <eth_address>")
            sys.exit(1)

    if not from_block:
        from_block = Ebb.get_block_number() - cfg.ONE_DAY_BLOCK_DURATION

    is_provider = True
    watch_fn = Path.home() / ".ebloc-broker" / f"watch_{eth_address}.out"
    _log.ll.LOG_FILENAME = watch_fn
    # open("watch.out", "w").close()
    _console_clear()
    print(" * s t a r t i n g")
    while True:
        bn = Ebb.get_block_number()
        if not watch_only_jobs:
            providers_info = {}
            providers = Ebb.get_providers()
            for provider_addr in providers:
                providers_info[provider_addr] = Ebb.get_provider_info(provider_addr)

        if is_provider:
            event_filter = Ebb._eblocbroker.events.LogJob.createFilter(
                fromBlock=int(from_block),
                argument_filters={"provider": eth_address},
                toBlock="latest",
            )
        else:
            event_filter = Ebb._eblocbroker.events.LogJob.createFilter(
                fromBlock=int(from_block),
                argument_filters={"owner": eth_address},
                toBlock="latest",
            )

        columns = 80
        columns_size = int(int(columns) / 2 - 9)
        job_full = ""
        job_count = 0
        completed_count = 0
        for job in enumerate(event_filter.get_all_entries()):
            job_count += 1
            try:
                _args = job["args"]
            except:
                job = job[1]
                _args = job["args"]

            _job = Ebb.get_job_info(
                _args["provider"],
                _args["jobKey"],
                _args["index"],
                0,
                job["blockNumber"],
                is_print=False,
            )
            state_val = state.inv_code[_job["stateCode"]]
            _color = "magenta"
            if state_val == "COMPLETED":
                _color = "green"
                completed_count += 1

            job_full = (
                f" [bold blue]*[/bold blue] [bold]{_job['job_key']}[/bold] {_job['index']} {_job['provider']} "
                f"[bold {_color}]{state_val}[/bold {_color}]\n{job_full}"
            )

        if not watch_only_jobs:
            job_ruler = (
                "[green]" + "=" * columns_size + "[bold cyan] jobs [/bold cyan]" + "=" * columns_size + "[/green]"
            )
            job_full = f"{job_ruler}\n{job_full}".rstrip()
        else:
            job_full = job_full.rstrip()

        is_connected = Ebb.is_web3_connected()
        _console_clear()
        open(watch_fn, "w").close()
        log(
            f"\r==> {_date() } bn={bn} | web3={is_connected} | address={eth_address} | {completed_count}/{job_count}",
            "bold",
        )
        if not watch_only_jobs:
            providers = Ebb.get_providers()
            columns_size = int(int(columns) / 2 - 12)
            log("\r" + "=" * columns_size + "[bold cyan] providers [/bold cyan]" + "=" * columns_size, "green")
            for k, v in providers_info.items():
                log(f"** provider_address={k}", end="\r")
                log(v, end="\r")

        log(job_full, is_output=False)
        log()
        time.sleep(2)


if __name__ == "__main__":
    try:
        eth_address = None
        if len(sys.argv) == 2:
            eth_address = sys.argv[1]

        watch(eth_address)
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception as e:
        print_tb(e)
