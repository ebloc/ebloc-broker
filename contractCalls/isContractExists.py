#!/usr/bin/env python3

import sys, json
from os.path import expanduser

def isContractExists(w3=None):
    home     = expanduser("~")
    contract = json.loads(open(home + '/eBlocBroker/contractCalls/contract.json').read())    
    contractAddress = contract['address']

    if w3 is None:
        import os        
        from imports import getWeb3
        w3 = getWeb3()
        
    contractAddress = w3.toChecksumAddress(contractAddress)   
    if w3.eth.getCode(contractAddress) == '0x' or w3.eth.getCode(contractAddress) == b'':
        return False

    return True

if __name__ == '__main__':
    print('isContractExists=' + str(isContractExists()))
