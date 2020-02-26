#!/usr/bin/env python3

import sys
import traceback

import owncloud

import lib
from contract.scripts.lib import convertIpfsToBytes32, cost
from contractCalls.get_provider_info import get_provider_info
from imports import connect


def submitJob(
    provider,
    key,
    core_list,
    core_min_list,
    dataTransferIn_list,
    dataTransferOut,
    storageID_list,
    source_code_hashes,
    cache_types_list,
    storageHour_list,
    accountID,
    jobPriceValue,
    data_prices_set_blocknumber_list,
):
    eBlocBroker, w3 = connect()
    if eBlocBroker is None or w3 is None:
        return False, "E: web3 is not connected"

    provider = w3.toChecksumAddress(provider)
    _from = w3.toChecksumAddress(w3.eth.accounts[accountID])

    status, provider_info = get_provider_info(provider)

    print(f"Provider's availableCoreNum:{provider_info['availableCoreNum']}")
    print(f"Provider's priceCoreMin:{provider_info['priceCoreMin']}")
    # my_filter = eBlocBroker.events.LogProviderInfo.createFilter(fromBlock=provider_info['blockReadFrom'], toBlock=provider_info['blockReadFrom'] + 1)

    if not eBlocBroker.functions.doesProviderExist(provider).call():
        return (False, f"E: Requested provider's Ethereum Address {provider} does not registered.")

    blockReadFrom, orcid = eBlocBroker.functions.getRequesterInfo(_from).call()

    if not eBlocBroker.functions.doesRequesterExist(_from).call():
        return (False, f"E: Requester's Ethereum Address {_from} does not exist.")

    if not eBlocBroker.functions.isOrcIDVerified(_from).call():
        return (False, f"E: Requester's orcid: {orcid.decode('UTF')} is not verified.")

    """
    if lib.storageID_list.IPFS == storageID_list or lib.storageID_list.IPFS_MINILOCK == storageID_list:
       lib.is_ipfs_running()
       strVal = my_filter.get_all_entries()[0].args['ipfsAddress']nnn
       print('Trying to connect into ' + strVal)
       output = os.popen('ipfs swarm connect ' + strVal).read()
       if 'success' in output:
          print(output)
    """

    """
    print(source_code_hashes[0].encode('utf-8'))
    for i in range(len(source_code_hashes)):
        source_code_hashes[i] = source_code_hashes[i]
        if len(source_code_hashes[i]) != 32 and len(source_code_hashes[i]) != 0:
            return False, 'source_code_hashes should be 32 characters.'
    """
    if not source_code_hashes:
        return False, "E: sourceCodeHash list is empty."

    if len(key) != 46 and (
        lib.StorageID.IPFS.value == storageID_list or lib.StorageID.IPFS_MINILOCK.value == storageID_list
    ):
        return (
            False,
            "E: key's length does not match with its original length, it should be 46. Please check your key length",
        )

    if len(key) != 33 and lib.StorageID.GDRIVE.value == storageID_list:
        return (
            False,
            "E: key's length does not match with its original length, it should be 33. Please check your key length",
        )

    for idx, core in enumerate(core_list):
        if core > provider_info["availableCoreNum"]:
            return (False, f"E: Requested {core}, which is {core}, is greater than the provider's core number")
        if core_min_list[idx] == 0:
            return (False, "E: core_min_list[" + str(idx) + "] is provided as 0. Please provide non-zero value")

    for i in range(len(storageID_list)):
        if storageID_list[i] > 4:
            return (False, "E: Wrong storageID_list value is given. Please provide from 0 to 4")

    if len(key) >= 64:
        return (False, "E: Length of key is greater than 64, please provide lesser")

    for core_min in core_min_list:
        if core_min > 1440:
            return (False, "E: core_min_list provided greater than 1440. Please provide smaller value")

    print(cache_types_list)

    for cache_type in cache_types_list:
        if cache_type > 1:
            # cache_type = {0: private, 1: public}
            return (False, f"E: cachType ({cache_types_list[i]}) provided greater than 1. Please provide smaller value")

    # if len(jobDescription) >= 128:
    #    return 'Length of jobDescription is greater than 128, please provide lesser.'
    provider_price_block_number = eBlocBroker.functions.getProviderSetBlockNumbers(provider).call()[-1]
    args = [
        provider,
        provider_price_block_number,
        storageID_list,
        cache_types_list,
        data_prices_set_blocknumber_list,
        core_list,
        core_min_list,
        dataTransferOut,
    ]

    try:
        gasLimit = 4500000
        print(source_code_hashes)
        tx = eBlocBroker.functions.submitJob(
            key, dataTransferIn_list, args, storageHour_list, source_code_hashes
        ).transact({"from": _from, "value": jobPriceValue, "gas": gasLimit})
    except Exception:
        return False, traceback.format_exc()

    return True, str(tx.hex())


if __name__ == "__main__":
    eBlocBroker, w3 = connect()

    if len(sys.argv) == 10:
        provider = w3.toChecksumAddress(str(sys.argv[1]))
        key = str(sys.argv[2])
        core_list = int(sys.argv[3])
        core_min_list = int(sys.argv[4])
        dataTransfer = int(sys.argv[5])
        storageID_list = int(sys.argv[6])
        sourceCodeHash = str(sys.argv[7])
        storageHour_list = int(sys.argv[8])
        accountID = int(sys.argv[9])
    elif len(sys.argv) == 13:
        provider = w3.toChecksumAddress(str(sys.argv[1]))
        key = str(sys.argv[2])
        core_list = int(sys.argv[3])
        coreDayDuration = int(sys.argv[4])
        coreHour = int(sys.argv[5])
        core_min_list = int(sys.argv[6])
        dataTransferIn = int(sys.argv[7])
        dataTransferOut = int(sys.argv[8])
        storageID_list = int(sys.argv[9])
        sourceCodeHash = str(sys.argv[10])
        storageHour_list = int(sys.argv[11])
        accountID = int(sys.argv[12])
        core_min_list = core_min_list + coreHour * 60 + coreDayDuration * 1440
        dataTransfer = dataTransferIn + dataTransferOut
    else:
        # ================================================ REQUESTER Inputs for testing ================================================
        storageID_list = lib.StorageID.IPFS.value
        provider = w3.toChecksumAddress("0x57b60037b82154ec7149142c606ba024fbb0f991")  # netlab
        cache_types_list = lib.CacheType.PRIVATE.value  # default
        storageHour_list = []
        source_code_hashes = []
        core_min_list_list = []

        if storageID_list == lib.StorageID.IPFS.value:  # IPFS
            print("Submitting through IPFS...")
            key = "QmbL46fEH7iaccEayKpS9FZnkPV5uss4SFmhDDvbmkABUJ"  # 30 seconds job
            coreDayDuration = 0
            coreHour = 0
            core_min_list = 1
            core_min_list = core_min_list + coreHour * 60 + coreDayDuration * 1440
            core_min_list_list.append(core_min_list)

            # DataSourceCodes:
            ipfsBytes32 = convertIpfsToBytes32(key)
            source_code_hashes.append(w3.toBytes(hexstr=ipfsBytes32))
            storageHour_list.append(1)

            ipfsBytes32 = convertIpfsToBytes32("QmSYzLDW5B36jwGSkU8nyfHJ9xh9HLjMsjj7Ciadft9y65")  # data1/data.txt
            source_code_hashes.append(w3.toBytes(hexstr=ipfsBytes32))
            storageHour_list.append(1)
            cache_types_list = lib.CacheType.PUBLIC.value  # default
        elif storageID_list == lib.StorageID.EUDAT.value:
            print("Submitting through EUDAT")
            oc = owncloud.Client("https://b2drop.eudat.eu/")
            with open(lib.EBLOCPATH + "/eudatPassword.txt", "r") as content_file:
                password = content_file.read().strip()

            oc.login(lib.OC_USER_ID, password)
            sourceCodeHash = "00000000000000000000000000000000"
        elif storageID_list == lib.StorageID.GITHUB.value:
            print("Submitting through GitHub...")
            key = "avatar-lavventura=simpleSlurmJob"
            coreDayDuration = 0
            coreHour = 0
            core_min_list = 1
            sourceCodeHash = "acfd2fd8a1e9ccf031db0a93a861f6eb"

        core_list = [1]
        dataTransferIn_list = [1, 1]
        dataTransferOut = 1
        dataTransfer = [dataTransferIn_list, dataTransferOut]
        accountID = 0

    requester = w3.toChecksumAddress(w3.eth.accounts[accountID])
    jobPriceValue, cost = cost(
        core_list,
        core_min_list_list,
        provider,
        requester,
        source_code_hashes,
        dataTransferIn_list,
        dataTransferOut,
        storage_hour_list,
        storageHour_list,
        data_prices_set_blocknumber_list,
        eBlocBroker,
        w3,
        False,
    )

    status, result = submitJob(
        provider,
        key,
        core_list,
        core_min_list_list,
        dataTransferIn_list,
        dataTransferOut,
        storageID_list,
        source_code_hashes,
        cache_types_list,
        storageHour_list,
        accountID,
        jobPriceValue,
    )

    if not status:
        print(result)
        sys.exit()
    else:
        receipt = lib.get_tx_status(status, result)
        if receipt["status"] == 1:
            logs = eBlocBroker.events.LogJob().processReceipt(receipt)
            try:
                print("Job's index=" + str(logs[0].args["index"]))
            except IndexError:
                print("Transaction is reverted.")
