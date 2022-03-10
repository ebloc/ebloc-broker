#!/usr/bin/env python3

import sys
import time
from pathlib import Path

from broker import cfg
from broker._utils import _log
from broker._utils._log import _console_clear
from broker._utils.tools import _date, log, print_tb
from broker.lib import state

Ebb = cfg.Ebb
watch_only_jobs = True


def watch(eth_address="", from_block=None):
    # from_block = 13895443
    from_block = 13998718
    # if not eth_address:
    #     # TODO: pull from cfg
    #     eth_address = "0xeab50158e8e51de21616307a99c9604c1c453a02"

    is_provider = False
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

        if not from_block:
            from_block = cfg.Ebb.get_block_number() - cfg.BLOCK_DURATION_1_DAY

        if is_provider:
            event_filter = cfg.Ebb._eBlocBroker.events.LogJob.createFilter(
                fromBlock=int(from_block),
                argument_filters={"provider": eth_address},
                toBlock="latest",
            )
        else:
            event_filter = cfg.Ebb._eBlocBroker.events.LogJob.createFilter(
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

            _job = cfg.Ebb.get_job_info(
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
