#!/usr/bin/env python

from imports import *

clusterAddress = web3.toChecksumAddress(str(sys.argv[1])) 
print(eBlocBroker.functions.getClusterReceiptNode(clusterAddress, int(sys.argv[2])).call())

