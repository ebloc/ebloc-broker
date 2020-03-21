#!/usr/bin/env python3

import sys

import lib
from imports import connect


def is_transaction_passed(tx_hash):
    eBlocBroker, w3 = connect()
    if w3 is None:
        sys.exit(1)

    return lib.is_transaction_passed(w3, tx_hash)


if __name__ == "__main__":
    if len(sys.argv) == 2:
        tx_hash = str(sys.argv[1])
    else:
        sys.exit(1)

    print("is_transaction_passed=" + str(is_transaction_passed(tx_hash)))
