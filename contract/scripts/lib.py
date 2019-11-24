#!/usr/bin/env python3

import base58, binascii

ONE_HOUR_BLOCK_DURATION = 240
Qm = b'\x12'


class CacheType:
    PUBLIC = 0
    PRIVATE = 1

    
class StorageID:
    IPFS = 0
    EUDAT = 1
    IPFS_MINILOCK = 2
    GITHUB = 3
    GDRIVE = 4

    
class JobStateCodes:
    SUBMITTED = 0
    PENDING = 1
    RUNNING = 2
    REFUNDED = 3
    CANCELLED = 4
    COMPLETED = 5
    TIMEOUT = 6

    
def convertIpfsToBytes32(hash_string):
    bytes_array = base58.b58decode(hash_string)
    b = bytes_array[2:]
    return binascii.hexlify(b).decode("utf-8")


def cost(coreArray, coreMinArray, provider, requester, sourceCodeHash, dataTransferIn, dataTransferOut, cacheHour, storageID, cacheType, eB, w3, brownie=True):
    if brownie:
        providerPriceInfo = eB.getProviderInfo(provider, 0)
    else:
        providerPriceInfo = eB.functions.getProviderInfo(provider, 0).call()

    blockReadFrom = providerPriceInfo[0]
    availableCoreNum = providerPriceInfo[1]
    priceCoreMin = providerPriceInfo[2]
    priceDataTransfer = providerPriceInfo[3]
    priceStorage = providerPriceInfo[4]
    priceCache = providerPriceInfo[5]
    commitmentBlockNum = providerPriceInfo[6]

    assert len(coreArray)      == len(coreMinArray)
    assert len(sourceCodeHash) == len(cacheHour)
    assert len(cacheHour)      == len(storageID)
    assert len(cacheType)      == len(storageID)
    
    for i in range(len(storageID)):
        assert storageID[i] <= 4
        if storageID[i] == StorageID.IPFS:
            assert cacheType[i] == CacheType.PUBLIC

    jobPriceValue = 0
    computationalCost = 0
    cacheCost = 0
    storageCost = 0
    _dataTransferIn = 0
    
    for i in range(len(coreArray)):
        computationalCost += priceCoreMin * coreArray[i] * coreMinArray[i]

    for i in range(len(sourceCodeHash)):
        if brownie:
            jobReceivedBlocNumber, jobGasStorageHour, isUsed = eB.getJobStorageTime(provider, requester, sourceCodeHash[i])
        else:
            jobReceivedBlocNumber, jobGasStorageHour, isUsed = eB.functions.getJobStorageTime(provider, requester, sourceCodeHash[i]).call()

        if jobReceivedBlocNumber + jobGasStorageHour * ONE_HOUR_BLOCK_DURATION  < w3.eth.blockNumber:
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
          'computationalCost=' + str(computationalCost))

    cost = dict();
    cost['computationalCost'] = computationalCost
    cost['dataTransferCost']  = dataTransferCost
    cost['cacheCost']         = cacheCost
    cost['storageCost']       = storageCost

    return jobPriceValue, cost
