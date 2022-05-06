#!/usr/bin/env python3

"""Useful function for Brownie test."""

import datetime
from os import popen

from broker import cfg, config
from broker._utils.tools import log
from brownie import web3 as w3


def new_test():
    """Organize before new test."""
    try:
        *_, columns = popen("stty size", "r").read().split()
    except:
        columns = 20

    line = "-" * int(columns)
    print(f"\x1b[6;30;43m{line}\x1b[0m")


def mine(block_number):
    """Mine give block number in the brownie testing.

    You can only advance the time by whole seconds.

    __ https://stackoverflow.com/a/775075/2402577
    __ https://stackoverflow.com/a/775095/2402577
    """
    if block_number == cfg.ONE_HOUR_BLOCK_DURATION:
        log(f"## mining for {cfg.ONE_HOUR_BLOCK_DURATION} blocks...")

    seconds = block_number * cfg.BLOCK_DURATION
    height = w3.eth.blockNumber
    timestamp_temp = w3.eth.getBlock(height)["timestamp"]
    timedelta = cfg.BLOCK_DURATION * block_number
    config.chain.mine(blocks=int(block_number), timedelta=timedelta)
    timestamp_after = w3.eth.getBlock(w3.eth.blockNumber)["timestamp"]
    log(
        f"==> Mined {block_number} empty blocks | {datetime.timedelta(seconds=seconds)} | "
        f"{height} => {w3.eth.blockNumber} | "
        f"{timestamp_temp} => {timestamp_after} diff={timestamp_after - timestamp_temp}",
        "bold",
    )
    assert w3.eth.blockNumber == height + block_number and (timestamp_after - timestamp_temp) + 1 >= timedelta
