#!/usr/bin/env python3

import sys

from eblocbroker.Contract import Contract

if __name__ == "__main__":
    if len(sys.argv) == 2:
        address = str(sys.argv[1])
        print(Contract().get_balance(address))
    else:
        print("E: Please provide an address as argument")
