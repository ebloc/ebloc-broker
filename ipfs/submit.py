#!/usr/bin/env python3

import os
import sys

import eblocbroker.Contract as Contract
from config import env, logging
from contract.scripts.lib import Job, cost
from imports import connect
from lib import check_linked_data, get_tx_status, run, silent_remove
from libs import ipfs
from libs.ipfs import mlck_encrypt
from startup import bp  # noqa: F401
from utils import CacheType, StorageID, _colorize_traceback, generate_md5sum, ipfs_to_bytes32, printc

if __name__ == "__main__":
    eBlocBroker, w3 = connect()
    ebb = Contract.eblocbroker
    job = Job()

    printc("Attempt to submit a job", "blue")
    # requester inputs for testing
    account_id = 1
    provider = w3.toChecksumAddress("0x57b60037b82154ec7149142c606ba024fbb0f991")  # netlab

    job.storage_ids = [StorageID.IPFS, StorageID.IPFS]
    # storage_ids = [StorageID.IPFS_MINILOCK, StorageID.IPFS_MINILOCK]
    # storage_ids = [StorageID.IPFS_MINILOCK, StorageID.IPFS]

    main_storage_id = job.storage_ids[0]
    job.cache_types = [CacheType.PUBLIC, CacheType.PUBLIC]

    folders = []  # full paths are provided
    folders.append(f"{env.EBLOCPATH}/base/sourceCode")
    folders.append(f"{env.EBLOCPATH}/base/data/data1")

    path_to = f"{env.EBLOCPATH}/base/data_link"
    check_linked_data(None, path_to, folders[1:])
    for folder in folders:
        if not os.path.isdir(folder):
            print(f"{folder} path does not exist")
            sys.exit(1)

    if main_storage_id == StorageID.IPFS:
        printc("Submitting source code through IPFS...")
    elif main_storage_id == StorageID.IPFS_MINILOCK:
        printc("Submitting source code through IPFS_MINILOCK...")
    else:
        printc("Please provide IPFS or IPFS_MINILOCK storage type")
        sys.exit(1)

    for idx, folder in enumerate(folders):
        try:
            provider_info = ebb.get_provider_info(provider)
        except:
            sys.exit()

        target = folder
        if job.storage_ids[idx] == StorageID.IPFS_MINILOCK:
            # provider_minilock_id = provider_info["miniLockID"] # TODO: read from the provider
            provider_minilock_id = "SjPmN3Fet4bKSBJAutnAwA15ct9UciNBNYo1BQCFiEjHn"
            mlck_pass = "bright wind east is pen be lazy usual"
            try:
                target = mlck_encrypt(provider_minilock_id, mlck_pass, target)
                printc(f"minilock_file:{target}", "blue")
            except:
                sys.exit(1)

        try:
            ipfs_hash = ipfs.add(target)
            # ipfs_hash = ipfs.add(folder, True)  # True includes .git/
            run(["ipfs", "refs", ipfs_hash])
        except:
            sys.exit(1)

        if idx == 0:
            key = ipfs_hash

        job.source_code_hashes.append(ipfs_to_bytes32(ipfs_hash))
        printc(f"{target} \nipfs_hash:{ipfs_hash}  md5sum:{generate_md5sum(target)}\n", "green")
        if main_storage_id == StorageID.IPFS_MINILOCK:
            # created .minilock file is removed since its already in ipfs
            silent_remove(target)

    job.cores = [1]
    job.execution_durations = [1]
    job.storage_hours = [1, 1]
    job.dataTransferIns = [1, 1]  # TODO: calculate from the file itself
    job.dataTransferOut = 1
    job.data_prices_set_block_numbers = [0, 0]

    requester = w3.toChecksumAddress(w3.eth.accounts[account_id])
    job_price, _cost = cost(provider, requester, job, eBlocBroker, w3)
    try:
        receipt = get_tx_status(ebb.submit_job(provider, key, account_id, job_price, job))
        if receipt["status"] == 1:
            try:
                logs = eBlocBroker.events.LogJob().processReceipt(receipt)
                print(f"job_index={logs[0].args['index']}")
            except IndexError:
                logging.error("E: Transaction is reverted.")
    except:
        _colorize_traceback()
        sys.exit(1)
