#!/usr/bin/env python3

import sys 

def isRequesterExists(requesterAddress,eBlocBroker=None, web3=None):
    if eBlocBroker is None and web3 is None:
        from imports import connectEblocBroker, getWeb3
        web3        = getWeb3() 
        eBlocBroker = connectEblocBroker(web3)
        
    requesterAddress = web3.toChecksumAddress(requesterAddress) 
    return eBlocBroker.functions.isRequesterExists(requesterAddress).call() 

if __name__ == '__main__':
    if len(sys.argv) == 2:
        requesterAddress = str(sys.argv[1]) 
    else:
        requesterAddress = '0x4E4A0750350796164d8defc442a712b7557BF282'

    print(isRequesterExists(requesterAddress))   
