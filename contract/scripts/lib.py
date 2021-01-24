#!/usr/bin/env python3

"""Useful function for Brownie test."""

from os import popen

import broker.config as config
from broker._utils.tools import log
from brownie import web3 as w3

# sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))


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

    https://stackoverflow.com/a/775075/2402577
    """
    m, s = divmod(block_number * 15, 60)
    h, m = divmod(m, 60)
    height = w3.eth.blockNumber
    timestamp_temp = w3.eth.getBlock(height)["timestamp"]
    timedelta = 15 * block_number
    config.chain.mine(blocks=block_number, timedelta=timedelta)
    timestamp_after = w3.eth.getBlock(w3.eth.blockNumber)["timestamp"]
    log(
        f"==> Mined {block_number} empty blocks | {h:d}:{m:02d}:{s:02d} (h/m/s) | "
        f"{height} => {w3.eth.blockNumber} | "
        f"{timestamp_temp} => {timestamp_after} diff={timestamp_after - timestamp_temp}"
    )
    assert w3.eth.blockNumber == height + block_number and (timestamp_after - timestamp_temp) + 1 >= timedelta
