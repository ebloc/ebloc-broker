#!/usr/bin/env python3
import sys, os

sys.path.insert(1, os.path.join(sys.path[0], '..'))
import lib
from imports import getWeb3
web3 = getWeb3()

if __name__ == '__main__':
    if len(sys.argv) == 2:
        tx = str(sys.argv[1])
    else:
        tx = '0x8402f49c5d779930da79430a5c4dbc85e23c5020b9211650b595749ea16e74d1'
    print(lib.isTransactionPassed(web3, tx))
