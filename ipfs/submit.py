#!/usr/bin/env python3

import os
import sys

from config import bp, env, logging  # noqa: F401
from contract.scripts.lib import Job, cost
from contractCalls.get_provider_info import get_provider_info
from contractCalls.submitJob import submitJob
from imports import connect
from lib import CacheType, StorageID, check_linked_data, get_tx_status, printc, run, silent_remove
from libs import ipfs
from libs.ipfs import mlck_encrypt
from utils import _colorize_traceback, generate_md5sum, ipfs_to_bytes

if __name__ == "__main__":
    eBlocBroker, w3 = connect()
    job = Job()

    printc("Attempt to submit a job", "blue")
    # requester inputs for testing
    account_id = 1
    provider = w3.toChecksumAddress("0x57b60037b82154ec7149142c606ba024fbb0f991")  # netlab

    job.storage_ids = [StorageID.IPFS.value, StorageID.IPFS.value]
    # storage_ids = [StorageID.IPFS_MINILOCK.value, StorageID.IPFS_MINILOCK.value]
    # storage_ids = [StorageID.IPFS_MINILOCK.value, StorageID.IPFS.value]

    main_storageID = job.storage_ids[0]
    job.cache_types = [CacheType.PUBLIC.value, CacheType.PUBLIC.value]

    folders = []  # full paths are provided
    folders.append(f"{env.EBLOCPATH}/base/sourceCode")
    folders.append(f"{env.EBLOCPATH}/base/data/data1")

    path_to = f"{env.EBLOCPATH}/base/data_link"
    check_linked_data(None, path_to, folders[1:])
    for folder in folders:
        if not os.path.isdir(folder):
            print(f"{folder} path does not exist")
            sys.exit(1)

    if main_storageID == StorageID.IPFS.value:
        printc("Submitting source code through IPFS...")

    if main_storageID == StorageID.IPFS_MINILOCK.value:
        printc("Submitting source code through IPFS_MINILOCK...")

    for idx, folder in enumerate(folders):
        try:
            provider_info = get_provider_info(provider)
        except:
            sys.exit()

        target = folder
        if job.storage_ids[idx] == StorageID.IPFS_MINILOCK.value:
            # provider_minilock_id = provider_info["miniLockID"] # TODO: read from the provider
            provider_minilock_id = "SjPmN3Fet4bKSBJAutnAwA15ct9UciNBNYo1BQCFiEjHn"
            mlck_pass = "bright wind east is pen be lazy usual"
            success, target = mlck_encrypt(provider_minilock_id, mlck_pass, target)
            if not success:
                sys.exit(1)
            printc(f"minilock_file:{target}", "blue")

        success, ipfs_hash = ipfs.add(target)
        # success, ipfs_hash = ipfs.add(folder, True)  # True includes .git/
        try:
            run(["ipfs", "refs", ipfs_hash])
        except:
            sys.exit(1)

        md5sum = generate_md5sum(target)
        if idx == 0:
            key = ipfs_hash

        job.source_code_hashes.append(ipfs_to_bytes(ipfs_hash))
        printc(f"{target} \nipfs_hash:{ipfs_hash}  md5sum:{md5sum}\n", "green")
        if main_storageID == StorageID.IPFS_MINILOCK.value:
            # created .minilock file is removed since its already in ipfs
            silent_remove(target)

    job.cores = [1]
    job.core_execution_durations = [1]
    job.storage_hours = [1, 1]
    job.dataTransferIns = [1, 1]  # TODO: calculate from the file itself
    job.dataTransferOut = 1
    job.data_prices_set_block_numbers = [0, 0]

    requester = w3.toChecksumAddress(w3.eth.accounts[account_id])
    job_price, _cost = cost(provider, requester, job, eBlocBroker, w3)
    try:
        receipt = get_tx_status(submitJob(provider, key, account_id, job_price, job))
        if receipt["status"] == 1:
            try:
                logs = eBlocBroker.events.LogJob().processReceipt(receipt)
                print(f"Job index={logs[0].args['index']}")
            except IndexError:
                logging.error("E: Transaction is reverted.")
    except:
        print(_colorize_traceback())
        sys.exit(1)


"""
            if len(sys.argv) == 10:
        pass
        provider = w3.toChecksumAddress(str(sys.argv[1]))
        key = str(sys.argv[2])
        job.cores = int(sys.argv[3])
        job.core_execution_durations = int(sys.argv[4])
        job.dataTransfer = int(sys.argv[5])
        job.storage_ids = int(sys.argv[6])
        job.sourceCodeHash = str(sys.argv[7])
        job.storage_hours = int(sys.argv[8])
        job.account_id = int(sys.argv[9])

    elif len(sys.argv) == 13:
        pass

        provider = w3.toChecksumAddress(str(sys.argv[1]))
        key = str(sys.argv[2])
        job.cores = int(sys.argv[3])
        coreDayDuration = int(sys.argv[4])
        coreHour = int(sys.argv[5])
        job.core_execution_durations = int(sys.argv[6])
        job.dataTransferIns = int(sys.argv[7])
        job.dataTransferOut = int(sys.argv[8])
        job.storage_ids = int(sys.argv[9])
        sourceCodeHash = str(sys.argv[10])
        storage_hours = int(sys.argv[11])
        account_id = int(sys.argv[12])
        core_execution_durations = core_execution_durations + coreHour * 60 + coreDayDuration * 1440

    else:
"""
