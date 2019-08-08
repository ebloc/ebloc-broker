#!/usr/bin/env python3

import sys

def isProviderExists(providerAddress, eBlocBroker=None, web3=None):
    if eBlocBroker is None and web3 is None:
        import os
        from imports import connectEblocBroker, getWeb3
        web3           = getWeb3()
        eBlocBroker    = connectEblocBroker(web3)

    providerAddress = web3.toChecksumAddress(providerAddress)        
    return eBlocBroker.functions.isProviderExists(providerAddress).call()
    
if __name__ == '__main__':
    if len(sys.argv) == 2:
        providerAddress = str(sys.argv[1])
        print(isProviderExists(providerAddress))
    else:
        print('Please provide provider address as argument.')        
