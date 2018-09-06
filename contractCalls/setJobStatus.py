#!/usr/bin/env python

from imports import *

jobKey    = str(sys.argv[1]) 
index     = int(sys.argv[2]) 
stateID   = int(sys.argv[3]) 
startTime = int(sys.argv[4]) 

tx = eBlocBroker.transact({"from":web3.toChecksumAddress(lib.CLUSTER_ID), "gas": 4500000}).setJobStatus(jobKey, index, stateID, startTime) 
print(tx.hex()) 
