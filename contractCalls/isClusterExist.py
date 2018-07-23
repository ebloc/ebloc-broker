#!/usr/bin/env python

from imports import *

if __name__ == '__main__': #{    
    if(len(sys.argv) == 2):
        clusterAddress = str(sys.argv[1]);
    else:
        clusterAddress = "0xda1E61E853bB8D63B1426295f59cb45A34425B63";
        
    clusterAddress = web3.toChecksumAddress(clusterAddress);
    print(str(eBlocBroker.functions.isClusterExist(clusterAddress).call()).rstrip('\n'));
#}
