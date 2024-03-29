#!/usr/bin/env python3

import consoledraw
import time

from broker import cfg
from broker._utils.tools import _date, log
from broker.config import env
from broker.lib import state

Ebb = cfg.Ebb
ETH_ADDRESS = "0x3e6FfC5EdE9ee6d782303B2dc5f13AFeEE277AeA"
console = consoledraw.Console()


def main():
    # os.system("cls" if os.name == "nt" else "printf '\033c'")
    block_number = Ebb.get_block_number()
    providers_info = {}
    providers = Ebb.get_providers()
    for provider_addr in providers:
        providers_info[provider_addr] = Ebb.get_provider_info(provider_addr)

    jobs = []
    from_block = cfg.Ebb.get_block_number() - cfg.ONE_DAY_BLOCK_DURATION
    event_filter = cfg.Ebb._eblocbroker.events.LogJob.createFilter(
        fromBlock=int(from_block),
        argument_filters={"owner": ETH_ADDRESS},
        toBlock="latest",
    )
    logged_jobs = event_filter.get_all_entries()
    for job in reversed(logged_jobs):
        job_info = cfg.Ebb.get_job_info(
            job["args"]["provider"], job["args"]["jobKey"], job["args"]["index"], 0, job["blockNumber"], is_print=False
        )
        jobs.append(job_info)

    is_connected = Ebb.is_web3_connected()
    while True:
        with console:
            log(
                f"\r * {_date() } latest_block_number={block_number} | is_web3_connected={is_connected}",
                "bold",
                end="",
            )
            if env.IS_TESTNET:
                log(f" | network=[g]BLOXBERG\n{providers}", "bold")

            columns = 80
            columns_size = int(int(columns) / 2 - 12)
            log("\r" + "=" * columns_size + "[bold cyan] providers [/bold cyan]" + "=" * columns_size, "g")
            for k, v in providers_info.items():
                log(f"\r** provider_address={k}")
                log(v)

            columns_size = int(int(columns) / 2 - 9)
            log("\r" + "=" * columns_size + "[bold cyan] jobs [/bold cyan]" + "=" * columns_size, "g")
            for job in jobs:
                log(
                    f"\r==> {job['job_key']} {job['index']} {job['provider']} "
                    f"{state.inv_code[job['stateCode']]}({job['stateCode']})"
                )

            time.sleep(1)
            block_number = Ebb.get_block_number()
            providers_info = {}
            providers = Ebb.get_providers()
            for provider_addr in providers:
                providers_info[provider_addr] = Ebb.get_provider_info(provider_addr)

            jobs = []
            from_block = cfg.Ebb.get_block_number() - cfg.ONE_DAY_BLOCK_DURATION
            event_filter = cfg.Ebb._eblocbroker.events.LogJob.createFilter(
                fromBlock=int(from_block),
                argument_filters={"owner": ETH_ADDRESS},
                toBlock="latest",
            )
            logged_jobs = event_filter.get_all_entries()
            for job in reversed(logged_jobs):
                job_info = cfg.Ebb.get_job_info(
                    job["args"]["provider"],
                    job["args"]["jobKey"],
                    job["args"]["index"],
                    0,
                    job["blockNumber"],
                    is_print=False,
                )
                jobs.append(job_info)

            is_connected = Ebb.is_web3_connected()
            providers = Ebb.get_providers()


if __name__ == "__main__":
    main()
