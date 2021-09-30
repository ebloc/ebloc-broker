#!/usr/bin/env python3

import sys

import broker.eblocbroker.Contract as Contract
from broker._utils.tools import log

if __name__ == "__main__":
    Ebb: "Contract.Contract" = Contract.EBB()
    if len(sys.argv) == 2:
        address = str(sys.argv[1])
        print(Ebb.get_balance(address))
    else:
        log("E: Provide an address as an argument")
