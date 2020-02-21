#!/usr/bin/env python3

import config
from imports import connect_to_web3


def blockNumber():
    if config.w3 is None:
        config.w3 = connect_to_web3()
        if not config.w3:
            return False

    return str(config.w3.eth.blockNumber).rstrip()


if __name__ == "__main__":
    print(blockNumber())
