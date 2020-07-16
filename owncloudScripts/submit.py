#!/usr/bin/env python3

import pprint
import sys
import time

import eblocbroker.Contract as Contract
import libs.eudat as eudat
import libs.git as git
from config import env
from contract.scripts.lib import Job, cost
from imports import connect
from lib import get_tx_status
from utils import CacheType, StorageID, _colorize_traceback, log, printc

eBlocBroker, w3 = connect()
Ebb = Contract.eblocbroker


def submit(provider, account_id):
    job = Job()

    provider = w3.toChecksumAddress(provider)
    provider_info = Ebb.get_provider_info(provider)
    print(f"provider[fID]={str(provider_info['f_id'])}")

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
            folder_hash = eudat.initialize_folder(folder)
        except:
            _colorize_traceback()
            sys.exit(1)

        if idx == 0:
            job_key = folder_hash

        # required to send string as bytes
        job.source_code_hashes.append(w3.toBytes(text=folder_hash))
        if not eudat.share_single_folder(folder_hash, provider_info["f_id"]):
            sys.exit(1)

        time.sleep(0.1)

    printc("\nSubmitting the job")
    job.execution_durations = [5]
    job.cores = [1]
    job.dataTransferIns = [1, 1]
    job.dataTransferOut = 1

    job.storage_ids = [StorageID.EUDAT, StorageID.EUDAT]
    job.cache_types = [CacheType.PRIVATE, CacheType.PUBLIC]
    job.storage_hours = [1, 1]
    job.data_prices_set_block_numbers = [0, 0]
    print(job.source_code_hashes)
    requester = w3.toChecksumAddress(w3.eth.accounts[account_id])

    job_price, _cost = cost(provider, requester, job, eBlocBroker, w3)
    try:
        return Ebb.submit_job(provider, job_key, account_id, job_price, job)
    except Exception as e:
        _colorize_traceback()
        if type(e).__name__ == "QuietExit":
            log(f"E: Unlock your Ethereum Account => web3.eth.accounts[{account_id}]", "red")
            log("In order to unlock an account you can use: ~/eBlocPOA/client.sh", "yellow")
        sys.exit(1)


if __name__ == "__main__":
    oc_requester = "059ab6ba-4030-48bb-b81b-12115f531296"
    account_id = 1  # different account than provider
    eudat.login(oc_requester, f"{env.LOG_PATH}/.eudat_client.txt", env.OC_CLIENT_REQUESTER)

    if len(sys.argv) == 3:
        provider = str(sys.argv[1])
        tar_hash = sys.argv[2]
        print(f"provided_hash={tar_hash}")
    else:
        # provider = "0x57b60037b82154ec7149142c606ba024fbb0f991"  # netlab
        provider = "0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49"  # home-vm

    try:
        tx_hash = submit(provider, account_id)
        receipt = get_tx_status(tx_hash)
        if receipt["status"] == 1:
            logs = eBlocBroker.events.LogJob().processReceipt(receipt)
            pprint.pprint(vars(logs[0].args))
            try:
                log(f"Job's index={logs[0].args['index']}")
                log("SUCCESS", "green")
            except IndexError:
                print("Transaction is reverted")
    except Exception:
        _colorize_traceback()
        sys.exit(1)
