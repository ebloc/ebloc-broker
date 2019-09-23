#!/usr/bin/env python3

import sys, lib
from imports import connect, getWeb3

def isTransactionPassed(tx_hash, eBlocBroker=None, w3=None):
    eBlocBroker, w3 = connect(eBlocBroker, w3)
    if eBlocBroker is None or w3 is None:
        sys.exit()

    return lib.isTransactionPassed(w3, tx_hash)
    
if __name__ == '__main__': 
    if len(sys.argv) == 2:
        tx_hash = str(sys.argv[1])
    else:
        sys.exit()

    print('isTransactionPassed=' + str(isTransactionPassed(tx_hash)))    
