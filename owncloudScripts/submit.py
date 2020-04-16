#!/usr/bin/env python3

import sys
import time

import libs.eudat as eudat
import libs.git as git
from config import bp  # noqa: F401
from contract.scripts.lib import Job, cost
from contractCalls.get_provider_info import get_provider_info
from contractCalls.submitJob import submitJob
from imports import connect
from lib import CacheType, StorageID, get_tx_status, printc
from settings import init_env
from utils import _colorize_traceback

env = init_env()


def submit(provider, oc):
    eBlocBroker, w3 = connect()
    job = Job()

    provider = w3.toChecksumAddress(provider)
    provider_info = get_provider_info(provider)
    account_id = 1  # different account than provider

    # full path of the sourceCodeFolders is given
    job.folders_to_share.append(f"{env.EBLOCPATH}/base/sourceCode")
    job.folders_to_share.append(f"{env.EBLOCPATH}/base/data/data1")

    if not git.is_repo(job.folders_to_share):
        return False, ""

    for idx, folder in enumerate(job.folders_to_share):
        if idx != 0:
            print("")

        printc(folder, "green")
        try:
            git.initialize_check(folder)
            git.commit_changes(folder)
        except:
            sys.exit(1)

        try:
            folder_hash = eudat.initialize_folder(folder, oc)
        except Exception as error:
            print(f"E: {error}")
            sys.exit(1)

        if idx == 0:
            job_key = folder_hash

        # required to send string as bytes
        job.source_code_hashes.append(w3.toBytes(text=folder_hash))
        if not eudat.share_single_folder(folder_hash, oc, provider_info["fID"]):
            sys.exit(1)
        time.sleep(0.1)

    printc("\nSubmitting Job...")
    job.core_execution_durations.append(5)
    job.cores = [1]
    job.dataTransferIns = [1, 1]
    job.dataTransferOut = 1

    job.storage_ids = [StorageID.EUDAT.value, StorageID.EUDAT.value]
    job.cache_types = [CacheType.PRIVATE.value, CacheType.PUBLIC.value]
    job.storage_hours = [1, 1]
    job.data_prices_set_block_numbers = [0, 0]
    print(job.source_code_hashes)
    requester = w3.toChecksumAddress(w3.eth.accounts[account_id])

    job_price, _cost = cost(provider, requester, job, eBlocBroker, w3, False)
    try:
        return submitJob(provider, job_key, account_id, job_price, job)
    except:
        print(_colorize_traceback())
        raise


if __name__ == "__main__":
    eBlocBroker, w3 = connect()
    oc = eudat.login("059ab6ba-4030-48bb-b81b-12115f531296", f"{env.LOG_PATH}/eudat_password.txt", env.OC_CLIENT,)

    # oc = owncloud.Client("https://b2drop.eudat.eu/")
    # oc.login("059ab6ba-4030-48bb-b81b-12115f531296", "qPzE2-An4Dz-zdLeK-7Cx4w-iKJm9")

    if len(sys.argv) == 3:
        provider = str(sys.argv[1])
        tar_hash = sys.argv[2]
        print(f"provided_hash={tar_hash}")
    else:
        provider = "0x57b60037b82154ec7149142c606ba024fbb0f991"  # netlab
        # provider = "0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49"  # home-vm

    try:
        tx_hash = submit(provider, oc)
        receipt = get_tx_status(tx_hash)
        if receipt["status"] == 1:
            logs = eBlocBroker.events.LogJob().processReceipt(receipt)
            try:
                print(f"Job's index={logs[0].args['index']}")
            except IndexError:
                print("Transaction is reverted.")
    except:
        print(_colorize_traceback())
        sys.exit(1)
