#!/usr/bin/env python3

import sys
import time

from config import bp, EBLOCPATH  # noqa: F401
from contract.scripts.lib import cost
from contractCalls.get_provider_info import get_provider_info
from contractCalls.submitJob import submitJob
from imports import connect
from lib import HOME, CacheType, StorageID, get_tx_status, printc
from lib_git import git_commit_changes, is_git_repo
from lib_owncloud import (eudat_initialize_folder, eudat_login,
                          share_single_folder)


def eudat_submit_job(provider, oc):  # fc33e7908fdf76f731900e9d8a382984
    eBlocBroker, w3 = connect()
    if eBlocBroker is None:
        return False, "eBlocBroker is not connected"

    if w3 is None:
        return False, "web3 is not connected"

    provider = w3.toChecksumAddress(provider)  # netlab
    success, provider_info = get_provider_info(provider)
    account_id = 1  # Different account than provider

    folder_to_share_list = []  # Path of folder to share
    source_code_hashes = []
    storage_hour_list = []
    core_min_list = []

    # Full path of the sourceCodeFolders is given
    folder_to_share_list.append(f"{EBLOCPATH}/base/sourceCode")
    folder_to_share_list.append(f"{EBLOCPATH}/base/data/data1")

    success = is_git_repo(folder_to_share_list)
    if not success:
        return False, ""

    for idx, folder in enumerate(folder_to_share_list):
        if idx != 0:
            print("")

        printc(folder, "green")
        success = git_commit_changes(folder)
        if not success:
            sys.exit(1)

        try:
            folder_hash = eudat_initialize_folder(folder, oc)
        except Exception as error:
            print(f"E: {error}")
            sys.exit(1)

        if idx == 0:
            job_key = folder_hash

        source_code_hash = w3.toBytes(text=folder_hash)  # required to send string as bytes
        source_code_hashes.append(source_code_hash)
        if not share_single_folder(folder_hash, oc, provider_info["fID"]):
            sys.exit(1)

        time.sleep(0.1)

    printc("\nSubmitting Job...")
    core_min_list.append(5)
    core_list = [1]
    dataTransferIn_list = [1, 1]
    dataTransferOut = 1

    storageID_list = [StorageID.EUDAT.value, StorageID.EUDAT.value]
    cache_types = [CacheType.PRIVATE.value, CacheType.PUBLIC.value]
    storage_hour_list = [1, 1]
    data_prices_set_blocknumber_list = [0, 0]
    print(source_code_hashes)
    requester = w3.toChecksumAddress(w3.eth.accounts[account_id])
    job_price_value, _cost = cost(
        core_list,
        core_min_list,
        provider,
        requester,
        source_code_hashes,
        dataTransferIn_list,
        dataTransferOut,
        storage_hour_list,
        storageID_list,
        cache_types,
        data_prices_set_blocknumber_list,
        eBlocBroker,
        w3,
        False,
    )

    success, output = submitJob(
        provider,
        job_key,
        core_list,
        core_min_list,
        dataTransferIn_list,
        dataTransferOut,
        storageID_list,
        source_code_hashes,
        cache_types,
        storage_hour_list,
        account_id,
        job_price_value,
        data_prices_set_blocknumber_list,
    )
    return success, output


if __name__ == "__main__":
    eBlocBroker, w3 = connect()
    oc = eudat_login(
        "059ab6ba-4030-48bb-b81b-12115f531296", f"{HOME}/eBlocBroker/owncloudScripts/p.txt", ".oc_client.pckl",
    )

    # oc = owncloud.Client("https://b2drop.eudat.eu/")
    # oc.login("059ab6ba-4030-48bb-b81b-12115f531296", "qPzE2-An4Dz-zdLeK-7Cx4w-iKJm9")

    if len(sys.argv) == 3:
        provider = str(sys.argv[1])
        tar_hash = sys.argv[2]
        print(f"provided_hash={tar_hash}")
    else:
        # provider = "0x57b60037b82154ec7149142c606ba024fbb0f991"  # netlab
        provider = "0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49"  # home-vm

    success, output = eudat_submit_job(provider, oc)
    if not success:
        print(output)
        sys.exit(1)
    else:
        receipt = get_tx_status(success, output)
        if receipt["status"] == 1:
            logs = eBlocBroker.events.LogJob().processReceipt(receipt)
            try:
                print(f"Job's index={logs[0].args['index']}")
            except IndexError:
                print("Transaction is reverted.")
