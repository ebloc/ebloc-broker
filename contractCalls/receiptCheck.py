#!/usr/bin/env python3

import sys, os, lib, traceback
from lib import PROVIDER_ID
from imports import connect

# tx = eB.processPayment(jobKey, [index, jobID], executionTimeMin, resultIpfsHash, endTime, dataTransfer, sourceCodeHashArray, {"from": accounts[0]})

def processPayment(jobKey, index, jobID, executionTimeMin, resultIpfsHash, storageID, endTime, dataTransfer, sourceCodeHashArray, eBlocBroker=None, w3=None):    
    eBlocBroker, w3 = connect(eBlocBroker, w3)
    _from = w3.toChecksumAddress(PROVIDER_ID)

    if len(resultIpfsHash) != 46 and (lib.StorageID.IPFS.value == storageID or lib.StorageID.IPFS_MINILOCK.value == storageID):
        return False, "jobKey's length does not match with its original length. Please check your jobKey"
    
    try:
        resultIpfsHash = w3.toBytes(hexstr=lib.convertIpfsToBytes32(resultIpfsHash)) # resultIpfsHash is converted into byte32 format
        
        tx = eBlocBroker.functions.processPayment(jobKey, [int(index), int(jobID)], int(executionTimeMin), resultIpfsHash, int(endTime), dataTransfer, sourceCodeHashArray).transact({"from": _from, "gas": 4500000})
    except Exception:
        return False, traceback.format_exc()
    
    return True, tx.hex()

if __name__ == '__main__': 
    if len(sys.argv) == 10:
        jobKey           = str(sys.argv[1]) 
        index            = int(sys.argv[2])
        jobID            = int(sys.argv[3])
        executionTimeMin = int(sys.argv[4]) 
        resultIpfsHash   = str(sys.argv[5]) 
        storageID        = int(sys.argv[6]) 
        endTime          = int(sys.argv[7])
        dataTransfer     = [int(sys.argv[8]), int(sys.argv[9])]
        sourceCodeHashArray = []
    else: # Dummy call        
        jobKey           = 'QmY6jUjufnyB2nZe38hRZvmyboxtzRcPkP388Yjfhuomoy' 
        index            = 4
        jobID            = 0
        executionTimeMin = 1
        resultIpfsHash   = '0x'
        storageID        = 0
        endTime          = 1128590
        dataTransfer     = [0, 0]
        sourceCodeHashArray = [b'\x93\xa52\x1f\x93\xad\\\x9d\x83\xb5,\xcc\xcb\xba\xa59~\xc3\x11\xe6%\xd3\x8d\xfc+"\x185\x03\x90j\xd4'] # should pull from the job event

    status, result = processPayment(jobKey, index, jobID, executionTimeMin, resultIpfsHash, storageID, endTime, dataTransfer, sourceCodeHashArray)
    if status:
        print('tx_hash=' + result)        
    else:
        print(result)
