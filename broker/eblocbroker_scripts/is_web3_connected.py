#!/usr/bin/env python3

import sys

from broker import cfg
from broker._utils.tools import print_tb

if __name__ == "__main__":
    Ebb = cfg.Ebb
    try:
        print(Ebb.is_web3_connected())
        # print(Ebb.is_web3_connected())
    except Exception as e:
        print_tb(e)
        sys.exit(1)
