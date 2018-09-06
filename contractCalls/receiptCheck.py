#!/usr/bin/env python

from imports import *

jobKey           = str(sys.argv[1]) 
index            = int(sys.argv[2]) 
jobRunTimeMinute = int(sys.argv[3]) 
resultIpfsHash   = str(sys.argv[4]) 
storageID        = int(sys.argv[5]) 
endTime          = int(sys.argv[6]) 

tx = eBlocBroker.transact({"from":web3.toChecksumAddress(lib.CLUSTER_ID), "gas": 4500000}).receiptCheck(jobKey, index, jobRunTimeMinute, resultIpfsHash, storageID, endTime) 
print('Tx: ' + tx.hex()) 
