#!/usr/bin/env python3
import config
from imports import connect_to_web3


def blockNumber():
    if config.w3 is None:
        connect_to_web3()

    return str(config.w3.eth.blockNumber).replace("\n", "")


if __name__ == "__main__":
    print(blockNumber())
