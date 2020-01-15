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


def getJobStorageTime(eB, provider, source_code_hash, brownie=False):
    if brownie:
        ret = eB.getJobStorageTime(provider,  source_code_hash)
    else:
        ret = eB.functions.getJobStorageTime(provider,  source_code_hash).call()

    receivedBlock = ret[0]
    cacheDuration = ret[1]
    is_private = ret[2]
    isVerified_Used = ret[3]
    return receivedBlock, cacheDuration, is_private, isVerified_Used


def convertIpfsToBytes32(hash_string):
    bytes_array = base58.b58decode(hash_string)
    b = bytes_array[2:]
    return binascii.hexlify(b).decode("utf-8")


def cost(coreArray, coreMinArray, provider, requester, sourceCodeHash, dataTransferIn, dataTransferOut, cacheHour, storageID, cacheType, data_prices_set_blocknumber_array, eB, w3, brownie=True):
    print('\nEntered into cost calculation...')
    block_number =  w3.eth.blockNumber

    if brownie:
        providerPriceInfo = eB.getProviderInfo(provider, 0)
    else:
        providerPriceInfo = eB.functions.getProviderInfo(provider, 0).call()

    # blockReadFrom = providerPriceInfo[0]
    _providerPriceInfo = providerPriceInfo[1]
    # availableCoreNum = _providerPriceInfo[0]
    # commitmentBlockDuration = _providerPriceInfo[1]
    priceCoreMin = _providerPriceInfo[2]
    priceDataTransfer = _providerPriceInfo[3]
    priceStorage = _providerPriceInfo[4]
    priceCache = _providerPriceInfo[5]

    assert len(coreArray) == len(coreMinArray)
    assert len(sourceCodeHash) == len(cacheHour)
    assert len(cacheHour) == len(storageID)
    assert len(cacheType) == len(storageID)

    for i in range(len(storageID)):
        assert storageID[i] <= 4
        if storageID[i] == StorageID.IPFS:
            assert cacheType[i] == CacheType.PUBLIC

    jobPriceValue = 0
    computationalCost = 0
    cacheCost = 0
    storageCost = 0
    dataTransferIn_sum = 0

    # Calculating the computational cost
    for i in range(len(coreArray)):
        computationalCost += priceCoreMin * coreArray[i] * coreMinArray[i]

    # Calculating the cache cost
    for i in range(len(sourceCodeHash)):
        source_code_hash = sourceCodeHash[i]
        print(source_code_hash)

        receivedBlock, cacheDuration, is_private, isVerified_Used = getJobStorageTime(eB, provider, source_code_hash, brownie)
        if brownie:
            received_storage_deposit = eB.getReceivedStorageDeposit(provider, requester, source_code_hash)
        else:
            received_storage_deposit = eB.functions.getReceivedStorageDeposit(provider, requester, source_code_hash).call() # TODO: prc de hata veriyor

        print(not is_private)
        print(receivedBlock + cacheDuration >= block_number)
        if received_storage_deposit > 0 or (receivedBlock + cacheDuration >= block_number and not is_private and isVerified_Used):
            pass
        else:
            if data_prices_set_blocknumber_array[i] > 0:  # If true, registered data's price should be considered for storage
                res = eB.getRegisteredDataPrice(provider, source_code_hash, data_prices_set_blocknumber_array[i])
                dataPrice = res[0]
                storageCost += dataPrice
                break

            if receivedBlock + cacheDuration * ONE_HOUR_BLOCK_DURATION < w3.eth.blockNumber:
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
