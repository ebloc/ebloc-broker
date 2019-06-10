#!/usr/bin/env python3

import sys

def getClusterReceiptNode(clusterAddress, index, eBlocBroker=None, web3=None):
    if eBlocBroker is None and web3 is None:
        import os
        from imports import connectEblocBroker, getWeb3
        web3        = getWeb3()
        eBlocBroker = connectEblocBroker(web3)

    clusterAddress = web3.toChecksumAddress(clusterAddress) 
    return eBlocBroker.functions.getClusterReceiptNode(clusterAddress, index).call()

if __name__ == '__main__':
    if len(sys.argv) == 2:
        clusterAddress = str(sys.argv[1])
        print(isClusterExist(clusterAddress))
    else:
        clusterAddress = '0x4e4a0750350796164d8defc442a712b7557bf282'
        index = 0;
        
    print(getClusterReceiptNode(clusterAddress, index))
