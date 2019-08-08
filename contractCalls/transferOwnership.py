#!/usr/bin/env python3

import sys, os
from isAddress import isAddress

def transferOwnership(newOwner, eBlocBroker=None, web3=None):
    if eBlocBroker is None and web3 is None:
        from imports import connectEblocBroker, getWeb3
        web3           = getWeb3()
        eBlocBroker    = connectEblocBroker(web3)

    import lib
    if newOwner == '0x0000000000000000000000000000000000000000':
        return False, 'Provided address is zero.'

    if not web3.isAddress(newOwner):
        return False, 'Provided address is not valid.'

    newOwner = web3.toChecksumAddress(newOwner)
    tx = eBlocBroker.transact({"from": web3.toChecksumAddress(lib.PROVIDER_ID), "gas": 4500000}).transferOwnership(newOwner)
    return True, tx.hex()

if __name__ == '__main__':
    if len(sys.argv) == 2:
        newOwner  = str(sys.argv[1])
        status, result = transferOwnership(newOwner)
        if status:
            print('Tx_hash: ' + result)
        else:
            print(result)
    else:
        print('Please provide the newOwner address as argument.')             
