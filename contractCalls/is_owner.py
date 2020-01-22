#!/usr/bin/env python3

# Example To run: ./is_owner.py 0x57b60037b82154ec7149142c606ba024fbb0f991

import sys
from get_owner import get_owner


def is_owner(addr) -> bool:
    """
    Checks if the given address is the owner of the contract.
    """
    return addr.lower() == get_owner().lower()


if __name__ == '__main__':
    if len(sys.argv) == 2:
        addr = str(sys.argv[1])
        print(is_owner(addr))
    else:
        print('Please provide an Ethereum address as an argument.')
