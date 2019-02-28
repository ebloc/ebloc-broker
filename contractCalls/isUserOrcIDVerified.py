#!/usr/bin/env python3

import sys

def isUserOrcIDVerified(userAddress, eBlocBroker=None):
    if eBlocBroker is None:
        import os
        sys.path.insert(1, os.path.join(sys.path[0], '..'))
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
        userAddress = "0x4e4a0750350796164D8DefC442a712B7557BF282"
        
    print(isUserOrcIDVerified(userAddress))
