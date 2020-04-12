#!/usr/bin/env python3

import sys

from imports import connect
from utils import _colorize_traceback


def get_owner():
    eBlocBroker, w3 = connect()
    return eBlocBroker.functions.getOwner().call()


if __name__ == "__main__":
    try:
        print(get_owner())
    except:
        print(_colorize_traceback())
        sys.exit()
