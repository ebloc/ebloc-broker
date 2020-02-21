#!/usr/bin/env python3

import pprint
import sys
import time

import owncloud

from contract.scripts.lib import cost
from contractCalls.get_provider_info import get_provider_info
from contractCalls.submitJob import submitJob
from imports import connect
from lib import CacheType, StorageID
from lib_owncloud import eudat_initialize_folder, singleFolderShare

# from lib_owncloud import isOcMounted


def eudat_submit_job(provider, oc):  # fc33e7908fdf76f731900e9d8a382984
    accountID = 1  # Different account than provider
    eBlocBroker, w3 = connect()
    if eBlocBroker is None or w3 is None:
        return False, "web3 is not connected"

    # if not isOcMounted():
    #     return False, 'owncloud is not connected'

    provider = w3.toChecksumAddress(provider)  # netlab
    status, provider_info = get_provider_info(provider)

    folder_to_share_list = []  # Path of folder to share
    source_code_hash_list = []
    storageHour_list = []
    coreMin_list = []

    # Full path of the sourceCodeFolders is given
    folder_to_share_list.append("/home/netlab/eBlocBroker/owncloudScripts/exampleFolderToShare/sourceCode")
    folder_to_share_list.append("/home/netlab/eBlocBroker/owncloudScripts/exampleFolderToShare/data1")

    for idx, folder in enumerate(folder_to_share_list):
        folder_hash = eudat_initialize_folder(folder, oc)
        if idx == 0:
            jobKey = folder_hash

        sourceCodeHash = w3.toBytes(text=folder_hash)  # required to send string as bytes
        source_code_hash_list.append(sourceCodeHash)
        if not singleFolderShare(folder_hash, oc, provider_info["fID"]):
            sys.exit()
        time.sleep(1)

    print("\nSubmitting Job...")
    coreMin_list.append(5)
    core_list = [1]
    dataTransferIn_list = [1, 1]
    dataTransferOut = 1

    storageID_list = [StorageID.EUDAT.value, StorageID.EUDAT.value]
    cacheType_list = [CacheType.PUBLIC.value, CacheType.PUBLIC.value]
    storageHour_list = [0, 0]
    data_prices_set_blocknumber_list = [0, 0]
    print(source_code_hash_list)

    requester = w3.toChecksumAddress(w3.eth.accounts[accountID])
    jobPriceValue, _cost = cost(
        core_list,
        coreMin_list,
        provider,
        requester,
        source_code_hash_list,
        dataTransferIn_list,
        dataTransferOut,
        storageHour_list,
        storageID_list,
        cacheType_list,
        data_prices_set_blocknumber_list,
        eBlocBroker,
        w3,
        False,
    )

    status, result = submitJob(
        provider,
        jobKey,
        core_list,
        coreMin_list,
        dataTransferIn_list,
        dataTransferOut,
        storageID_list,
        source_code_hash_list,
        cacheType_list,
        storageHour_list,
        accountID,
        jobPriceValue,
        data_prices_set_blocknumber_list,
    )
    return status, result


if __name__ == "__main__":
    eBlocBroker, w3 = connect()
    oc = owncloud.Client("https://b2drop.eudat.eu/")
    oc.login("059ab6ba-4030-48bb-b81b-12115f531296", "qPzE2-An4Dz-zdLeK-7Cx4w-iKJm9")

    if len(sys.argv) == 3:
        provider = str(sys.argv[1])
        tarHash = sys.argv[2]
        print("Provided hash=" + tarHash)
    else:
        provider = "0x57b60037b82154ec7149142c606ba024fbb0f991"  # netlab

    status, result = eudat_submit_job(provider, oc)
    if not status:
        print(result)
        sys.exit()
    else:
        print("tx_hash=" + result)
        receipt = w3.eth.waitForTransactionReceipt(result)
        print("Transaction receipt mined: \n")
        pprint.pprint(dict(receipt))
        print("Was transaction successful?")
        pprint.pprint(receipt["status"])
        if receipt["status"] == 1:
            logs = eBlocBroker.events.LogJob().processReceipt(receipt)
            try:
                print("Job's index=" + str(logs[0].args["index"]))
            except IndexError:
                print("Transaction is reverted.")
