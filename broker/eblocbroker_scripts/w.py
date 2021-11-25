#!/usr/bin/env python3

import time

import consoledraw

from broker import cfg
from broker._utils.tools import _time, log
from broker.config import env
from broker.lib import state

Ebb = cfg.Ebb
ETH_ADDRESS = "0x3e6FfC5EdE9ee6d782303B2dc5f13AFeEE277AeA"
console = consoledraw.Console()


# os.system("cls" if os.name == "nt" else "printf '\033c'")
block_number = Ebb.get_block_number()
providers_info = {}
providers = Ebb.get_providers()
for provider_addr in providers:
    providers_info[provider_addr] = Ebb.get_provider_info(provider_addr)

jobs = []
from_block = cfg.Ebb.get_block_number() - cfg.BLOCK_DURATION_1_DAY
event_filter = cfg.Ebb._eBlocBroker.events.LogJob.createFilter(
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
providers = Ebb.get_providers()
while True:
    with console:
        log(
            f"\r * {_time() } latest_block_number={block_number} | is_web3_connected={is_connected}",
            "bold",
            end="",
        )
        if env.IS_BLOXBERG:
            log(f" | network=[green]BLOXBERG\n{providers}", "bold")

        columns = 80
        columns_size = int(int(columns) / 2 - 12)
        log("\r" + "=" * columns_size + "[bold cyan] providers [/bold cyan]" + "=" * columns_size, "green")
        for k, v in providers_info.items():
            log(f"\r** provider_address={k}")
            log(v)

        columns_size = int(int(columns) / 2 - 9)
        log("\r" + "=" * columns_size + "[bold cyan] jobs [/bold cyan]" + "=" * columns_size, "green")
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
        from_block = cfg.Ebb.get_block_number() - cfg.BLOCK_DURATION_1_DAY
        event_filter = cfg.Ebb._eBlocBroker.events.LogJob.createFilter(
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
