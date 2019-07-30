#!/usr/bin/env python3

import sys, json
from os.path import expanduser

def isContractExist(web3=None):
    home     = expanduser("~")
    contract = json.loads(open(home + '/eBlocBroker/contractCalls/contract.json').read())    
    contractAddress = contract['address']

    if web3 is None:
        import os        
        from imports import getWeb3
        web3 = getWeb3()
        
    contractAddress = web3.toChecksumAddress(contractAddress)   
    if web3.eth.getCode(contractAddress) == '0x' or web3.eth.getCode(contractAddress) == b'':
        return False
    else:
        return True

if __name__ == '__main__':
    print(isContractExist())
