#!/usr/bin/env python3

import sys, os
import lib

def receiptCheck(jobKey, index, jobRunTimeMinute, resultIpfsHash, storageID, endTime, dataTransferIn, dataTransferSum, eBlocBroker=None, web3=None): 
    if (storageID == 0 and len(resultIpfsHash) != 46) or (storageID == 2 and len(resultIpfsHash) != 46):
        return False, "jobKey's length does not match with its original length. Please check your jobKey."
    
    if eBlocBroker is None and web3 is None:
        from imports import connectEblocBroker
        from imports import getWeb3
        web3        = getWeb3()
        eBlocBroker = connectEblocBroker(web3)
        
    tx = eBlocBroker.transact({"from":web3.toChecksumAddress(lib.PROVIDER_ID),
                               "gas": 4500000}).receiptCheck(str(jobKey), int(index), int(jobRunTimeMinute),
                                                             str(resultIpfsHash), int(storageID), int(endTime),
                                                             int(dataTransferIn), int(dataTransferSum)) 
    return True, 'Tx_hash: ' + tx.hex()

if __name__ == '__main__': 
    if len(sys.argv) == 8:
        jobKey           = str(sys.argv[1]) 
        index            = int(sys.argv[2]) 
        jobRunTimeMinute = int(sys.argv[3]) 
        resultIpfsHash   = str(sys.argv[4]) 
        storageID        = int(sys.argv[5]) 
        endTime          = int(sys.argv[6])
        dataTransferIn   = int(sys.argv[7])
        dataTransferSum  = int(sys.argv[8])
    else: # Dummy call        
        jobKey           = '231037324805864425899587012070500513653' 
        index            = 0
        jobRunTimeMinute = 1
        resultIpfsHash   = 'QmRsaBEGcqxQcJbBxCi1LN9iz5bDAGDWR6Hx7ZvWqgqmdR'
        storageID        = 0
        endTime          = 1128590
        dataTransferIn   = 50
        dataTransferSum  = 100
    
    print(receiptCheck(jobKey, index, jobRunTimeMinute, resultIpfsHash, storageID, endTime, dataTransferIn, dataTransferSum))
