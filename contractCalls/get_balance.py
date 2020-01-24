#!/usr/bin/env python3

import sys


def get_balance(address, eBlocBroker=None, web3=None):
    if eBlocBroker is not None and web3 is not None:
        address = web3.toChecksumAddress(address)
        return str(eBlocBroker.functions.balanceOf(address).call()).rstrip("\n")
    else:
        from imports import connectEblocBroker, getWeb3

        web3 = getWeb3()
        address = web3.toChecksumAddress(address)
        eBlocBroker = connectEblocBroker(web3)
        return str(eBlocBroker.functions.balanceOf(address).call()).rstrip("\n")


if __name__ == "__main__":
    if len(sys.argv) == 2:
        address = str(sys.argv[1])
        print(get_balance(address))
    else:
        print("Please provide an address as argument.")
