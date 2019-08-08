#!/usr/bin/env python3

import sys
from getOwner import getOwner

def isOwner(addr):
    return addr.lower() == getOwner().lower()
    
if __name__ == '__main__':
    if len(sys.argv) == 2:
        addr = str(sys.argv[1]) 
        print(isOwner(addr))
    else:
        print('Please provide an address.')
