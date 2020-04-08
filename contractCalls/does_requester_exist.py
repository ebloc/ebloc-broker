#!/usr/bin/env python3

import sys

from imports import connect


def does_requester_exist(address):
    eBlocBroker, w3 = connect()
    address = w3.toChecksumAddress(address)
    return eBlocBroker.functions.doesRequesterExist(address).call()


if __name__ == "__main__":
    if len(sys.argv) == 2:
        requester = str(sys.argv[1])
    else:
        requester = "0x57b60037B82154eC7149142c606bA024fBb0f991"

    print(does_requester_exist(requester))
