#!/usr/bin/env python3

import sys

def isUserOrcIDVerified(userAddress, eBlocBroker=None):
    if eBlocBroker is None:
        import os
        from imports import connectEblocBroker
        eBlocBroker = connectEblocBroker()

    if eBlocBroker.functions.isUserOrcIDVerified(userAddress).call() == 0:
        return 'False'
    else:
        return 'True'
    
if __name__ == '__main__': 
    if len(sys.argv) == 2:
        userAddress = str(sys.argv[1]) 
    else:
        userAddress = '0x57b60037B82154eC7149142c606bA024fBb0f991'
        
    print(isUserOrcIDVerified(userAddress))
