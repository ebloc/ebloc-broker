#!/usr/bin/env python3

import sys
from os.path import expanduser

def isContractExist(web3=None):
    home     = expanduser("~")
    address = open(home + '/eBlocBroker/contractCalls/address.json', "r")

    if web3 is None:
        import os
        sys.path.insert(1, os.path.join(sys.path[0], '..'))
        from imports import getWeb3
        web3 = getWeb3()
    contractAddress = web3.toChecksumAddress(address.read().replace("\n", ""))

    if web3.eth.getCode(contractAddress) == '0x' or web3.eth.getCode(contractAddress) == b'':
        return False
    else:
        return True

if __name__ == '__main__':
    print(isContractExist())
