#!/usr/bin/env python

from imports import *

if __name__ == '__main__': #{
    if(len(sys.argv) == 2):
        clusterAddress = str(sys.argv[1]);
    else:        
        clusterAddress = "0x4e4a0750350796164D8DefC442a712B7557BF282"; #POA

    print(web3.isAddress('0x4e4a0750350796164D8DefC442a712B7557BF282'));
#}

