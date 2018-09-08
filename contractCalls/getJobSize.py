#!/usr/bin/env python

import sys

def getJobSize(clusterAddress, eBlocBroker=None, web3=None): #{
    if eBlocBroker == None and web3 == None: #{
        import os
        sys.path.insert(1, os.path.join(sys.path[0], '..'))
        from imports import connectEblocBroker
        from imports import getWeb3
        web3           = getWeb3()
        eBlocBroker    = connectEblocBroker(web3)
    #}

    clusterAddress = web3.toChecksumAddress(clusterAddress) 
    return eBlocBroker.call().getJobSize(clusterAddress, jobKey)
#}
    
if __name__ == '__main__': #{
    if len(sys.argv) == 3:
        clusterAddress = str(sys.argv[1]) 
        jobKey         = str(sys.argv[2]) 
    else:
        clusterAddress = "0x4e4a0750350796164d8defc442a712b7557bf282" 
        jobKey         = "153802737479941507912962421857730686964" 

    print(getJobSize(clusterAddress))
#}
