#!/usr/bin/env python3

import sys
import time

from broker import cfg
from broker._utils import _log
from broker._utils._log import _console_clear
from broker._utils.tools import _time, log, print_tb
from broker.config import env
from broker.lib import state

Ebb = cfg.Ebb
ETH_ADDRESS = "0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49"
_log.ll.LOG_FILENAME = "watch.out"


def main():
    _console_clear()
    while True:
        block_number = Ebb.get_block_number()
        providers_info = {}
        providers = Ebb.get_providers()
        for provider_addr in providers:
            providers_info[provider_addr] = Ebb.get_provider_info(provider_addr)

        from_block = cfg.Ebb.get_block_number() - cfg.BLOCK_DURATION_1_DAY
        event_filter = cfg.Ebb._eBlocBroker.events.LogJob.createFilter(
            fromBlock=int(from_block),
            argument_filters={"owner": ETH_ADDRESS},
            toBlock="latest",
        )
        logged_jobs = event_filter.get_all_entries()
        columns = 80
        columns_size = int(int(columns) / 2 - 9)
        job_full = ""
        for job in logged_jobs:
            _job = cfg.Ebb.get_job_info(
                job["args"]["provider"],
                job["args"]["jobKey"],
                job["args"]["index"],
                0,
                job["blockNumber"],
                is_print=False,
            )
            job_full = (
                f"[bold blue]==>[/bold blue] [bold]{_job['job_key']}[/bold] {_job['index']} {_job['provider']} "
                f"[bold magenta]{state.inv_code[_job['stateCode']]}[/bold magenta]\n{job_full}"
            )

        job_ruler = "[green]" + "=" * columns_size + "[bold cyan] jobs [/bold cyan]" + "=" * columns_size + "[/green]"
        job_full = f"{job_ruler}\n{job_full}".rstrip()
        is_connected = Ebb.is_web3_connected()
        providers = Ebb.get_providers()
        _console_clear()
        open("watch.out", "w").close()
        log(
            f"\r * {_time() } latest_block_number={block_number} | is_web3_connected={is_connected}",
            "bold",
            end="",
        )
        if env.IS_BLOXBERG:
            log(f" | network=[green]BLOXBERG\n{providers}", "bold")

        columns_size = int(int(columns) / 2 - 12)
        log("\r" + "=" * columns_size + "[bold cyan] providers [/bold cyan]" + "=" * columns_size, "green")
        for k, v in providers_info.items():
            log(f"** provider_address={k}", end="\r")
            log(v, end="\r")

        log(job_full)
        time.sleep(2)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception as e:
        print_tb(e)