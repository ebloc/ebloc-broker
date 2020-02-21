#!/usr/bin/env python3

import sys

from imports import connect


def get_balance(address):
    eBlocBroker, w3 = connect()
    address = w3.toChecksumAddress(address)
    return str(eBlocBroker.functions.balanceOf(address).call()).rstrip()


if __name__ == "__main__":
    if len(sys.argv) == 2:
        address = str(sys.argv[1])
        print(get_balance(address))
    else:
        print("Please provide an address as argument.")
