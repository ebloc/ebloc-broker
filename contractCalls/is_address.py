#!/usr/bin/env python3

import sys

from imports import connect_to_web3


def is_address(addr, w3=None):
    if w3 is None:
        try:
            w3 = connect_to_web3()
            return w3.isAddress(addr)
        except:
            raise


if __name__ == "__main__":
    if len(sys.argv) == 2:
        provider = str(sys.argv[1])
    else:
        provider = "0x57b60037b82154ec7149142c606ba024fbb0f991"
    print(is_address(provider))
