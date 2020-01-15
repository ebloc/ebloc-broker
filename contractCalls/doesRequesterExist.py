#!/usr/bin/env python3

import sys 

def doesRequesterExist(requester,eBlocBroker=None, web3=None):
    if eBlocBroker is None and web3 is None:
        from imports import connectEblocBroker, getWeb3
        web3        = getWeb3() 
        eBlocBroker = connectEblocBroker(web3)
        
    requester = web3.toChecksumAddress(requester) 
    return eBlocBroker.functions.doesRequesterExist(requester).call() 

if __name__ == '__main__':
    if len(sys.argv) == 2:
        requester = str(sys.argv[1]) 
    else:
        requester = '0x57b60037B82154eC7149142c606bA024fBb0f991'

    print(doesRequesterExist(requester))   
