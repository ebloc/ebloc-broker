#!/usr/bin/env python3

import sys

def isRequesterOrcIDVerified(requesterAddress, eBlocBroker=None):
    if eBlocBroker is None:
        import os
        from imports import connectEblocBroker
        eBlocBroker = connectEblocBroker()

    if eBlocBroker.functions.isRequesterOrcIDVerified(requesterAddress).call() == 0:
        return 'False'
    else:
        return 'True'
    
if __name__ == '__main__': 
    if len(sys.argv) == 2:
        requesterAddress = str(sys.argv[1]) 
    else:
        requesterAddress = '0x57b60037B82154eC7149142c606bA024fBb0f991'
        
    print(isRequesterOrcIDVerified(requesterAddress))
