#!/usr/bin/env python3

"""Useful function for Brownie test."""

import datetime
from os import popen
from typing import Dict, List  # noqa

from broker import cfg, config
from broker._utils.tools import log
from brownie import web3 as w3

func_names = [
    "registerRequester",
    "registerProvider",
    "setJobStateRunning",
    "refund",
    "setDataVerified",
    "setDataVerified",
    "processPayment",
    "withdraw",
    "authenticateOrcID",
    "depositStorage",
    "updateProviderInfo",
    "updataDataPrice",
    "updateProviderPrices",
    "registerData",
    "refundStorageDeposit",
    "removeRegisteredData",
]


gas_costs = {}  # type: Dict[str, List[int]]
for func_name in func_names:
    gas_costs[func_name] = []


def new_test():
    """Organize before new test."""
    try:
        *_, columns = popen("stty size", "r").read().split()
    except:
        columns = 20

    line = "-" * int(columns)
    print(f"\x1b[6;30;43m{line}\x1b[0m")


def mine(bn):
    """Mine give block number in the brownie testing.

    You can only advance the time by whole seconds.

    __ https://stackoverflow.com/a/775075/2402577
    __ https://stackoverflow.com/a/775095/2402577
    """
    if bn == cfg.ONE_HOUR_BLOCK_DURATION:
        log(f"## mining for {cfg.ONE_HOUR_BLOCK_DURATION} blocks...")

    seconds = bn * cfg.BLOCK_DURATION
    height = w3.eth.blockNumber
    timestamp_temp = w3.eth.getBlock(height)["timestamp"]
    timedelta = cfg.BLOCK_DURATION * bn
    config.chain.mine(blocks=int(bn), timedelta=timedelta)
    timestamp_after = w3.eth.getBlock(w3.eth.blockNumber)["timestamp"]
    log(
        f"==> mined {bn} empty blocks | {datetime.timedelta(seconds=seconds)} | "
        f"{height} => {w3.eth.blockNumber} | "
        f"{timestamp_temp} => {timestamp_after} diff={timestamp_after - timestamp_temp}",
        "bold",
    )
    assert w3.eth.blockNumber == height + bn and (timestamp_after - timestamp_temp) + 1 >= timedelta
