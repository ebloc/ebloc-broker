#!/usr/bin/env python3

import sys

def isClusterExists(clusterAddress, eBlocBroker=None, web3=None):
    if eBlocBroker is None and web3 is None:
        import os
        from imports import connectEblocBroker, getWeb3
        web3           = getWeb3()
        eBlocBroker    = connectEblocBroker(web3)

    clusterAddress = web3.toChecksumAddress(clusterAddress)        
    return str(eBlocBroker.functions.isClusterExist(clusterAddress).call()).rstrip('\n')
    
if __name__ == '__main__':
    if len(sys.argv) == 2:
        clusterAddress = str(sys.argv[1])
        print(isClusterExist(clusterAddress))
    else:
        print('Please provide cluster address as argument.')        
