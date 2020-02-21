#!/usr/bin/env python3

import config
from imports import connect_to_web3


def is_web3_connected():
    if config.w3 is None:
        connect_to_web3()

    return config.w3.isConnected()


if __name__ == "__main__":
    print(is_web3_connected())
