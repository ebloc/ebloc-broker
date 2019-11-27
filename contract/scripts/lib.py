#!/usr/bin/env python3

import base58
import binascii

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
    NONE = 5


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


def cost(coreArray, coreMinArray, provider, requester, sourceCodeHash, dataTransferIn, dataTransferOut, cacheHour, storageID, cacheType,
         data_prices_set_blocknumber_array, eB, w3, brownie=True):
    if brownie:
        providerPriceInfo = eB.getProviderInfo(provider, 0)
    else:
        providerPriceInfo = eB.functions.getProviderInfo(provider, 0).call()

    blockReadFrom = providerPriceInfo[0]
    _providerPriceInfo = providerPriceInfo[1]
    availableCoreNum = _providerPriceInfo[0]
    commitmentBlockDuration = _providerPriceInfo[1]
    priceCoreMin = _providerPriceInfo[2]
    priceDataTransfer = _providerPriceInfo[3]
    priceStorage = _providerPriceInfo[4]
    priceCache = _providerPriceInfo[5]

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
    dataTransferIn_sum = 0

    for i in range(len(coreArray)):
        computationalCost += priceCoreMin * coreArray[i] * coreMinArray[i]

    for i in range(len(sourceCodeHash)):
        if brownie:
            ret = eB.getJobStorageTime(provider, requester, sourceCodeHash[i])
            
            jobSt, isUsed = eB.getJobStorageTime(provider, requester, sourceCodeHash[i])            
            jobReceivedBlocNumber = jobSt[0]
            jobGasStorageHour = jobSt[1]
        else:
            jobSt, isUsed = eB.functions.getJobStorageTime(provider, requester, sourceCodeHash[i]).call()
            jobReceivedBlocNumber = jobSt[0]
            jobGasStorageHour = jobSt[1]

        if data_prices_set_blocknumber_array[i] > 0:  # If true, registered data's price should be considered for storage
            res = eB.getRegisteredDataPrice(provider, sourceCodeHash[i], data_prices_set_blocknumber_array[i])
            dataPrice = res[0]
            storageCost += dataPrice
            break
    
        if jobReceivedBlocNumber + jobGasStorageHour * ONE_HOUR_BLOCK_DURATION < w3.eth.blockNumber:
            dataTransferIn_sum += dataTransferIn[i]
        if cacheHour[i] > 0:
            storageCost += priceStorage * dataTransferIn[i] * cacheHour[i]
        else:
            cacheCost += priceCache * dataTransferIn[i]

    dataTransferCost = priceDataTransfer * (dataTransferIn_sum + dataTransferOut)
    jobPriceValue = computationalCost + dataTransferCost + cacheCost + storageCost

    print('\njobPriceValue='   + str(jobPriceValue)       + ' == ' +
          'cacheCost='         + str(cacheCost)           + ' | ' +
          'storageCost='       + str(storageCost)         + ' | ' +
          'dataTransferCost='  + str(dataTransferCost)    + ' | ' +
          'computationalCost=' + str(computationalCost))

    cost = dict();
    cost['computationalCost'] = computationalCost
    cost['dataTransferCost'] = dataTransferCost
    cost['cacheCost'] = cacheCost
    cost['storageCost'] = storageCost

    return jobPriceValue, cost
