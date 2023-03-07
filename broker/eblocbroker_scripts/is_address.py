#!/usr/bin/env python3

import sys

from broker import cfg


def is_address():
    Ebb = cfg.Ebb
    if len(sys.argv) == 2:
        address = str(sys.argv[1])
    else:
        address = "0x57b60037b82154ec7149142c606ba024fbb0f991"

    is_address = Ebb.is_address(address)
    print(f"is_address={is_address}")


if __name__ == "__main__":
    is_address()
