#!/usr/bin/env python3

import binascii
from pdb import set_trace as bp

import base58

ONE_HOUR_BLOCK_DURATION = 240
Qm = b"\x12"


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
        ret = eB.getJobStorageTime(provider, source_code_hash)
    else:
        ret = eB.functions.getJobStorageTime(provider, source_code_hash).call()

    receivedBlock = ret[0]
    cacheDuration = ret[1]
    is_private = ret[2]
    is_verified_used = ret[3]
    return receivedBlock, cacheDuration, is_private, is_verified_used


def convertIpfsToBytes32(hash_string):
    bytes_array = base58.b58decode(hash_string)
    b = bytes_array[2:]
    return binascii.hexlify(b).decode("utf-8")


def cost(
    coreArray,
    coreMinArray,
    provider,
    requester,
    source_code_hashes,
    dataTransferIn,
    dataTransferOut,
    storage_hours,
    storageID_to_process,
    cache_types,
    data_prices_set_blocknumber_array,
    eB,
    w3,
    brownie=True,
):
    print("\nEntered into cost calculation...")
    block_number = w3.eth.blockNumber

    if brownie:
        provider_price_info = eB.getProviderInfo(provider, 0)
    else:
        provider_price_info = eB.functions.getProviderInfo(provider, 0).call()

    # blockReadFrom = provider_price_info[0]
    _provider_price_info = provider_price_info[1]
    # availableCoreNum = _provider_price_info[0]
    # commitmentBlockDuration = _provider_price_info[1]
    priceCoreMin = _provider_price_info[2]
    priceDataTransfer = _provider_price_info[3]
    priceStorage = _provider_price_info[4]
    priceCache = _provider_price_info[5]

    assert len(coreArray) == len(coreMinArray)
    assert len(source_code_hashes) == len(storage_hours)
    assert len(storage_hours) == len(storageID_to_process)
    assert len(cache_types) == len(storageID_to_process)

    for idx, storageID in enumerate(storageID_to_process):
        assert storageID <= 4
        if storageID == StorageID.IPFS:
            assert cache_types[idx] == CacheType.PUBLIC

    job_price_value = 0
    computationalCost = 0
    cacheCost = 0
    storageCost = 0
    dataTransferIn_sum = 0

    # Calculating the computational cost
    for idx, core in enumerate(coreArray):
        computationalCost += priceCoreMin * core * coreMinArray[idx]

    # Calculating the cache cost
    for idx, source_code_hash in enumerate(source_code_hashes):
        print(source_code_hash)
        receivedBlock, cacheDuration, is_private, is_verified_used = getJobStorageTime(
            eB, provider, source_code_hash, brownie
        )

        if brownie:
            received_storage_deposit = eB.getReceivedStorageDeposit(
                provider, requester, source_code_hash
            )
        else:
            received_storage_deposit = eB.functions.getReceivedStorageDeposit(provider, requester, source_code_hash).call()

        if receivedBlock + cacheDuration < w3.eth.blockNumber:
            # Storage time is completed
            received_storage_deposit = 0

        print(f"is_private:{is_private}")
        # print(receivedBlock + cacheDuration >= block_number)
        # if received_storage_deposit > 0 or
        if (received_storage_deposit > 0 and receivedBlock + cacheDuration >= w3.eth.blockNumber) or (
                receivedBlock + cacheDuration >= block_number and not is_private and is_verified_used
        ):
            print(f"For {source_code_hash} no storage_cost is paid")
            pass
        else:
            if (data_prices_set_blocknumber_array[idx] > 0):
                # If true, registered data's price should be considered for storage
                res = eB.getRegisteredDataPrice(
                    provider, source_code_hash, data_prices_set_blocknumber_array[idx]
                )
                dataPrice = res[0]
                storageCost += dataPrice
                break

            #  if received_storage_deposit == 0 and (receivedBlock + cacheDuration < w3.eth.blockNumber):
            if received_storage_deposit == 0:
                dataTransferIn_sum += dataTransferIn[idx]

                if storage_hours[idx] > 0:
                    storageCost += priceStorage * dataTransferIn[idx] * storage_hours[idx]
                else:
                    cacheCost += priceCache * dataTransferIn[idx]

    dataTransferCost = priceDataTransfer * (dataTransferIn_sum + dataTransferOut)
    job_price_value = computationalCost + dataTransferCost + cacheCost + storageCost
    print(
        f"\njob_price_value={job_price_value} <=> "
        f"cacheCost={cacheCost} | storageCost={storageCost} | dataTransferCost={dataTransferCost} | computationalCost={computationalCost}"
    )

    cost = dict()
    cost["computationalCost"] = computationalCost
    cost["dataTransferCost"] = dataTransferCost
    cost["cacheCost"] = cacheCost
    cost["storageCost"] = storageCost

    return job_price_value, cost
