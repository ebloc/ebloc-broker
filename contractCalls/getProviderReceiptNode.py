#!/usr/bin/env python3

import sys

def getProviderReceiptNode(providerAddress, index, eBlocBroker=None, web3=None):
    if eBlocBroker is None and web3 is None:
        import os
        from imports import connectEblocBroker, getWeb3
        web3        = getWeb3()
        eBlocBroker = connectEblocBroker(web3)

    providerAddress = web3.toChecksumAddress(providerAddress) 
    return eBlocBroker.functions.getProviderReceiptNode(providerAddress, index).call()

if __name__ == '__main__':
    if len(sys.argv) == 2:
        providerAddress = str(sys.argv[1])
        print(isProviderExists(providerAddress))
    else:
        providerAddress = '0x4e4a0750350796164d8defc442a712b7557bf282'
        index = 0;
        
    print(getProviderReceiptNode(providerAddress, index))
