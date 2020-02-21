#!/usr/bin/env python3

import sys

from imports import connect


def doesProviderExist(address):
    eBlocBroker, w3 = connect()
    address = w3.toChecksumAddress(address)
    return eBlocBroker.functions.doesProviderExist(address).call()


if __name__ == "__main__":
    if len(sys.argv) == 2:
        provider_address = str(sys.argv[1])
        print(doesProviderExist(provider_address))
    else:
        print("E: Please provide provider address as argument.")
