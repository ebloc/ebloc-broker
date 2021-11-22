#!/usr/bin/env python3

import os
import time

from broker import cfg
from broker._utils._log import _console_ruler
from broker._utils.tools import _time, delete_multiple_lines, log
from broker.config import env

Ebb = cfg.Ebb

os.system("cls" if os.name == "nt" else "printf '\033c'")
while True:
    block_number = Ebb.get_block_number()
    providers_info = {}
    providers = Ebb.get_providers()
    for provider_addr in providers:
        providers_info[provider_addr] = Ebb.get_provider_info(provider_addr)

    delete_multiple_lines(1000)
    log(
        f" * {_time() } latest_block_number={block_number} | is_web3_connected={Ebb.is_web3_connected()} | ",
        "bold",
        end="",
    )
    if env.IS_BLOXBERG:
        log("network=[green]BLOXBERG", "bold")

    _console_ruler("providers")
    log(Ebb.get_providers(), "bold")
    for k, v in providers_info.items():
        log(f"** provider_address={k}")
        log(v)

    _console_ruler("jobs")
    time.sleep(15)
    # os.system("cls" if os.name == "nt" else "printf '\033c'")
