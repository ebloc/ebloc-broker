#!/usr/bin/env python

from imports import *

if __name__ == '__main__': #{
    if len(sys.argv) == 3:
        clusterAddress = str(sys.argv[1]) 
        jobKey         = str(sys.argv[2]) 
    else:
        clusterAddress = "0x75a4c787c5c18c587b284a904165ff06a269b48c" 
        jobKey         = "QmRsaBEGcqxQcJbBxCi1LN9iz5bDAGDWR6Hx7ZvWqgqmdR" 

    clusterAddress = web3.toChecksumAddress(clusterAddress) 
    print(eBlocBroker.call().getJobSize(clusterAddress, jobKey)) 
#}
