#!/usr/bin/env python3

import sys

import eblocbroker.Contract as Contract

if __name__ == "__main__":
    Ebb = Contract.eblocbroker

    if len(sys.argv) == 2:
        provider = str(sys.argv[1])
    else:
        provider = "0x57b60037b82154ec7149142c606ba024fbb0f991"

    print(Ebb.is_address(provider))
