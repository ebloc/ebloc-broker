#!/usr/bin/env python3

import sys
from broker._utils.tools import log
import broker.cfg as cfg

if __name__ == "__main__":
    Ebb = cfg.Ebb
    if len(sys.argv) == 2:
        address = str(sys.argv[1])
        print(Ebb._get_balance(address))
    else:  # ./get_account_balance.py 0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49
        log("E: Please provide an address as argument")
