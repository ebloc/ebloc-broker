#!/usr/bin/env python3

import sys

def getClusterReceiptSize(clusterAddress, eBlocBroker=None, web3=None): #{
    if eBlocBroker == None and web3 == None: #{
        import os
        sys.path.insert(1, os.path.join(sys.path[0], '..'))
        from imports import connectEblocBroker
        from imports import getWeb3
        web3           = getWeb3()
        eBlocBroker    = connectEblocBroker(web3)
    #}

    clusterAddress = web3.toChecksumAddress(clusterAddress) 
    return eBlocBroker.functions.getClusterReceiptSize(clusterAddress).call()
    
#}

if __name__ == '__main__': #{
    if len(sys.argv) == 2:
        clusterAddress = str(sys.argv[1]) 
    else:        
        clusterAddress = "0x4e4a0750350796164D8DefC442a712B7557BF282"  #POA

    print(getClusterReceiptSize(clusterAddress))
#}
