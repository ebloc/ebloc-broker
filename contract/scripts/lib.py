#!/usr/bin/env python3

import base58, binascii

Qm = b'\x12'

class cacheType:
    private = 0
    public  = 1
    none    = 2
    ipfs    = 3

class storageID:
    ipfs  = 0
    eudat = 1
    ipfs_miniLock = 2
    github = 3
    gdrive = 4

def convertIpfsToBytes32(hash_string):
    bytes_array = base58.b58decode(hash_string)
    b = bytes_array[2:]
    return binascii.hexlify(b).decode("utf-8")

def cost(coreArray, coreMinArray, account, sourceCodeHash, dataTransferIn, dataTransferOut, cacheHour, storageID, eB, w3, brownie=True):
    if brownie:
        providerPriceInfo   = eB.getProviderInfo(account)
    else:
        providerPriceInfo   = eB.functions.getProviderInfo(account).call()

    blockReadFrom       = providerPriceInfo[0]
    availableCoreNum    = providerPriceInfo[1]
    priceCoreMin        = providerPriceInfo[2]
    priceDataTransfer   = providerPriceInfo[3]
    priceStorage        = providerPriceInfo[4]
    priceCache          = providerPriceInfo[5]
    commitmentBlockNum  = providerPriceInfo[6]

    assert len(coreArray) == len(coreMinArray)
    assert len(sourceCodeHash) == len(cacheHour)
    assert len(cacheHour) == len(storageID)

    for i in range(len(storageID)):
        assert(storageID[i] <= 4)

    jobPriceValue     = 0
    computationalCost = 0
    cacheCost         = 0
    storageCost       = 0
    _dataTransferIn   = 0

    for i in range(len(coreArray)):
        computationalCost += priceCoreMin * coreArray[i] * coreMinArray[i]

    for i in range(len(sourceCodeHash)):
        if brownie:
            jobReceivedBlocNumber, jobGasStorageHour = eB.getJobStorageTime(account, sourceCodeHash[i])
        else:
            jobReceivedBlocNumber, jobGasStorageHour = eB.functions.getJobStorageTime(account, sourceCodeHash[i]).call()

        if jobReceivedBlocNumber + jobGasStorageHour * 240 < w3.eth.blockNumber:
            _dataTransferIn += dataTransferIn[i]
            if cacheHour[i] > 0:
                storageCost += priceStorage * dataTransferIn[i] * cacheHour[i]
            else:
                cacheCost += priceCache * dataTransferIn[i]

    dataTransferCost = priceDataTransfer * (_dataTransferIn + dataTransferOut)
    jobPriceValue = computationalCost + dataTransferCost + cacheCost + storageCost

    print('\njobPriceValue='   + str(jobPriceValue)       + ' == ' +
          'cacheCost='         + str(cacheCost)           + ' | ' +
          'storageCost='       + str(storageCost)         + ' | ' +
          'dataTransferCost='  + str(dataTransferCost)    + ' | ' +
          'computationalCost=' + str(computationalCost)
    )

    cost = dict();
    cost['computationalCost'] = computationalCost
    cost['dataTransferCost']  = dataTransferCost
    cost['cacheCost']         = cacheCost
    cost['storageCost']       = storageCost

    return jobPriceValue, cost
