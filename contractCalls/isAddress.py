#!/usr/bin/env python3

import sys


def isAddress(addr, web3=None):
    if web3 is None:
        from imports import getWeb3

        web3 = getWeb3()

    if web3 == "notconnected":
        return web3

    return web3.isAddress(addr)


if __name__ == "__main__":
    if len(sys.argv) == 2:
        provider = str(sys.argv[1])
    else:
        provider = "0x57b60037b82154ec7149142c606ba024fbb0f991"
    print(isAddress(provider))
