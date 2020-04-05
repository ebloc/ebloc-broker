#!/usr/bin/env python3

import sys

import lib
from imports import connect_to_web3


def is_transaction_passed(tx_hash):
    w3 = connect_to_web3()
    if w3 is None:
        sys.exit(1)

    return lib.is_transaction_passed(tx_hash)


if __name__ == "__main__":
    if len(sys.argv) == 2:
        tx_hash = str(sys.argv[1])
    else:
        print("Please provide tx as an argument")
        sys.exit(1)

    print(f"is_transaction_passed={is_transaction_passed(tx_hash)}")
