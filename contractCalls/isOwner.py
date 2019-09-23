#!/usr/bin/env python3

# Example To run: ./isOwner.py 0x57b60037b82154ec7149142c606ba024fbb0f991

import sys
from getOwner import getOwner

def isOwner(addr) -> bool:
    """
    Checks if the given address is the owner of the contract.
    """
    return addr.lower() == getOwner().lower()
    
if __name__ == '__main__':
    if len(sys.argv) == 2:
        addr = str(sys.argv[1]) 
        print(isOwner(addr))
    else:
        print('Please provide an Ethereum address as an argument.')
