#!/usr/bin/env python3

import sys

if __name__ == "__main__":
    from eblocbroker.Contract import Contract

    c = Contract()

    if len(sys.argv) == 2:
        address = str(sys.argv[1])
        print(c.get_balance(address))
    else:
        print("Please provide an address as argument.")
