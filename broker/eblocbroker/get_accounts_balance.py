#!/usr/bin/env python3

import sys

import broker.eblocbroker.Contract as Contract
from broker._utils.tools import log

if __name__ == "__main__":
    Ebb: "Contract.Contract" = Contract.EBB()
    if len(sys.argv) == 2:
        address = str(sys.argv[1])
        print(Ebb._get_balance(address))
    else:  # ./get_account_balance.py 0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49
        log("E: Please provide an address as argument")
