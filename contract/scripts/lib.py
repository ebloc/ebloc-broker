#!/usr/bin/env python3

import base58, binascii

class cacheType:
    private = 0
    public = 1
    none = 2
    ipfs = 3

class storageID:
    ipfs = 0
    eudat = 1
    ipfs_miniLock = 2
    github = 3
    gdrive = 4

Qm = b'\x12 '

def convertIpfsToBytes32(hash_string):
    bytes_array = base58.b58decode(hash_string)
    b = bytes_array[2:]
    return binascii.hexlify(b).decode("utf-8")

def cost(coreArray, gasCoreMinArray, account, eB, sourceCodeHash, web3, dataTransferIn, dataTransferOut, gasStorageHour):
    blockReadFrom, coreLimit, priceCoreMin, priceDataTransfer, priceStorage, priceCache  = eB.getClusterInfo(account)
    assert len(coreArray) == len(gasCoreMinArray)

    computationalCost = 0
    for i in range(len(coreArray)):
        computationalCost += priceCoreMin * coreArray[i] * gasCoreMinArray[i]                           

    jobReceivedBlocNumber, jobGasStorageHour = eB.getJobStorageTime(account, sourceCodeHash)
    if jobReceivedBlocNumber + jobGasStorageHour * 240 > web3.eth.blockNumber:
        dataTransferIn = 0 # storageCost and cacheCost will be equaled to 0
                
    storageCost      = priceStorage * dataTransferIn * gasStorageHour
    cacheCost        = priceCache * dataTransferIn            
    dataTransferSum  = dataTransferIn + dataTransferOut
    dataTransferCost = priceDataTransfer * dataTransferSum           
    jobPriceValue     = computationalCost + dataTransferCost + storageCost + cacheCost
    return jobPriceValue
