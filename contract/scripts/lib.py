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

Qm = b'\x12'

def convertIpfsToBytes32(hash_string):
    bytes_array = base58.b58decode(hash_string)
    b = bytes_array[2:]
    return binascii.hexlify(b).decode("utf-8")

def cost(coreArray, coreMinArray, account, eB, sourceCodeHash, web3, dataTransferIn, dataTransferOut, cacheTime, sourceCodeSize):
    clusterPriceInfo   = eB.getClusterInfo(account)
    blockReadFrom      = clusterPriceInfo[0]
    availableCoreNum   = clusterPriceInfo[1]
    priceCoreMin       = clusterPriceInfo[2]
    priceDataTransfer  = clusterPriceInfo[3]
    priceStorage       = clusterPriceInfo[4]
    priceCache         = clusterPriceInfo[5]
    commitmentBlockNum = clusterPriceInfo[6]
   
    assert len(coreArray) == len(coreMinArray)

    computationalCost = 0
    for i in range(len(coreArray)):
        computationalCost += priceCoreMin * coreArray[i] * coreMinArray[i]                           

    # print(sourceCodeHash[0])
    for i in range(len(sourceCodeHash)):    
        jobReceivedBlocNumber, jobGasStorageHour = eB.getJobStorageTime(account, sourceCodeHash[i])
        if jobReceivedBlocNumber + jobGasStorageHour * 240 > web3.eth.blockNumber:
            dataTransferIn -= sourceCodeSize[i] # storageCost and cacheCost will be equaled to 0

    if dataTransferIn < 0:
        dataTransferIn = 0
        
    storageCost      = priceStorage * dataTransferIn * cacheTime[0]
    cacheCost        = priceCache * dataTransferIn            
    dataTransferSum  = dataTransferIn + dataTransferOut
    dataTransferCost = priceDataTransfer * dataTransferSum           
    jobPriceValue     = computationalCost + dataTransferCost + storageCost + cacheCost
    return jobPriceValue, dataTransferIn
