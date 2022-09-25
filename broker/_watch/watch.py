#!/usr/bin/env python3

"""Job watcher for the end of test."""

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

Ebb = cfg.Ebb
columns_size = 30
is_get_ongoing_test_results = False
is_log_to_file = True


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


def get_providers_info():
    # from broker.test_setup.user_set import providers
    providers_info = {}
    providers = Ebb.get_providers()
    for provider_addr in providers:
        providers_info[provider_addr] = Ebb.get_provider_info(provider_addr)

    providers = Ebb.get_providers()
    log("\r" + "=" * columns_size + "[bold] providers [/bold]" + "=" * columns_size, "green")
    for k, v in providers_info.items():
        log(f"** provider_address={k}", end="\r")
        log(v, end="\r")


def _watch(eth_address, from_block, is_provider):
    bn = Ebb.get_block_number()
    if is_provider:
        _argument_filters = {"provider": eth_address}
    else:
        _argument_filters = {"owner": eth_address}

    event_filter = Ebb._eblocbroker.events.LogJob.createFilter(
        fromBlock=int(from_block),
        argument_filters=_argument_filters,
        toBlock="latest",
    )
    header = f"   [bold yellow]{'{:<44}'.format('KEY')} INDEX STATUS[/bold yellow]"
    job_full = ""
    job_count = 0
    completed_count = 0
    workload_cppr_completed = 0
    workload_nas_completed = 0
    workload_cppr_count = 0
    workload_nas_count = 0
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
            is_fetch_code_hashes=True,
        )
        state_val = state.inv_code[_job["stateCode"]]
        c = "magenta"
        if state_val == "COMPLETED":
            c = "green"
            completed_count += 1

        if len(_job["code_hashes"]) == 4:
            workload_cppr_count += 1
            workload_type = "cppr"
            if state_val == "COMPLETED":
                workload_cppr_completed += 1
        elif len(_job["code_hashes"]) == 1:
            workload_nas_count += 1
            workload_type = "nas"
            if state_val == "COMPLETED":
                workload_nas_completed += 1
        else:
            print("ALERT")

        if is_get_ongoing_test_results:
            job_full = (
                f" [bold blue]*[/bold blue] [bold white]{'{:<48}'.format(_job['job_key'])}[/bold white] "
                f"{_job['index']} {workload_type} [bold {c}]{state_val}[/bold {c}]\n{job_full}"
            )
        else:
            job_full = (
                f" [bold blue]*[/bold blue] [bold white]{'{:<48}'.format(_job['job_key'])}[/bold white] "
                f"{_job['index']} {workload_type} [bold {c}]{state_val}[/bold {c}]"
            )
            log(job_full)

        time.sleep(0.2)

    if is_get_ongoing_test_results:
        job_full = f"{header}\n{job_full}".rstrip()
    else:
        job_ruler = "[green]" + "=" * columns_size + "[bold cyan] jobs [/bold cyan]" + "=" * columns_size + "[/green]"
        job_full = f"{job_ruler}\n{header}\n{job_full}".rstrip()

    is_connected = Ebb.is_web3_connected()
    if is_get_ongoing_test_results:
        _console_clear()

    log(
        f"\r==> {_date()} bn={bn} | web3={is_connected} | address={eth_address} | {completed_count}/{job_count}",
        "bold",
    )
    log(f"workload_cppr_count={workload_cppr_completed}/{workload_cppr_count}", "b")
    log(f"workload_nas_count={workload_nas_completed}/{workload_nas_count}", "b")
    # get_providers_info()
    log(job_full, is_output=False)


def watch(eth_address="", from_block=None):
    if not from_block:
        from_block = Ebb.get_block_number() - cfg.ONE_DAY_BLOCK_DURATION

    from_block = 15867616
    if not eth_address:
        try:
            eth_address = get_eth_address_from_cfg()
        except Exception as e:
            log(f"E: {e}\neth_address is empty, run as: ./watch.py <eth_address>")
            sys.exit(1)

    if is_log_to_file:
        watch_fn = Path.home() / ".ebloc-broker" / f"watch_{eth_address}.out"
        open(watch_fn, "w").close()
        _log.ll.LOG_FILENAME = watch_fn

    _console_clear()
    print(f" * starting for provider={eth_address}")
    is_provider = True

    if is_get_ongoing_test_results:
        while True:
            _watch(eth_address, from_block, is_provider)
            log()
            time.sleep(2)
    else:
        _watch(eth_address, from_block, is_provider)


def main():
    eth_address = None
    if len(sys.argv) == 2:
        eth_address = sys.argv[1]

    watch(eth_address)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception as e:
        print_tb(e)
