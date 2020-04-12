#!/usr/bin/env python3

import sys

import config
from imports import connect_to_web3
from utils import _colorize_traceback


def is_web3_connected():
    if config.w3 is None:
        connect_to_web3()

    return config.w3.isConnected()


if __name__ == "__main__":
    try:
        print(is_web3_connected())
    except:
        print(_colorize_traceback())
        sys.exit(1)
