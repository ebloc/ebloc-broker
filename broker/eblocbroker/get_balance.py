#!/usr/bin/env python3

import sys

import broker.cfg as cfg
from broker._utils.tools import log

if __name__ == "__main__":
    Ebb = cfg.Ebb
    if len(sys.argv) == 2:
        address = str(sys.argv[1])
        print(Ebb.get_balance(address))
    else:
        log("E: Provide an address as an argument")
