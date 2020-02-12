#!/usr/bin/env python3

import sys

import lib
from imports import connect_to_web3

w3 = connect_to_web3()

if __name__ == "__main__":
    if len(sys.argv) == 2:
        tx = str(sys.argv[1])
    else:
        tx = "0x8402f49c5d779930da79430a5c4dbc85e23c5020b9211650b595749ea16e74d1"

    print(lib.is_transaction_passed(tx))
