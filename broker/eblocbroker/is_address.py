#!/usr/bin/env python3

import sys

import broker.eblocbroker.Contract as Contract

if __name__ == "__main__":
    Ebb: "Contract.Contract" = Contract.EBB()
    if len(sys.argv) == 2:
        address = str(sys.argv[1])
    else:
        address = "0x57b60037b82154ec7149142c606ba024fbb0f991"

    print(Ebb.is_address(address))
