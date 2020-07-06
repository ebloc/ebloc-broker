#!/usr/bin/env python3

import os
import sys

import eblocbroker.Contract as Contract
from config import env, logging
from contract.scripts.lib import Job, cost
from imports import connect
from lib import check_linked_data, get_tx_status, run
from libs import ipfs
from libs.ipfs import gpg_encrypt
from utils import (
    CacheType,
    StorageID,
    _colorize_traceback,
    generate_md5sum,
    ipfs_to_bytes32,
    is_dpkg_installed,
    log,
    printc,
    silent_remove,
)

if __name__ == "__main__":
    printc("Attempt to submit a job.", "blue")
    eBlocBroker, w3 = connect()
    Ebb = Contract.eblocbroker
    job = Job()

    if not is_dpkg_installed("pigz"):
        log("E: Install pigz:\nsudo apt-get install pigz", "red")
        sys.exit()

    account_id = 1
    provider = w3.toChecksumAddress("0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49")  # netlab
    try:
        _from = Ebb.account_id_to_address(account_id)
    except:
        _colorize_traceback()
        sys.exit(1)

    if not Ebb.eBlocBroker.functions.doesRequesterExist(_from).call():
        log(f"E: Requester's Ethereum address {_from} is not registered", "red")
        sys.exit(1)

    *_, orcid = Ebb.eBlocBroker.functions.getRequesterInfo(_from).call()
    if not Ebb.eBlocBroker.functions.isOrcIDVerified(_from).call():
        log(f"E: Requester({_from})'s orcid: {orcid.decode('UTF')} is not verified", "red")
        sys.exit(1)

    # job.storage_ids = [StorageID.IPFS, StorageID.IPFS]
    job.storage_ids = [StorageID.IPFS_GPG, StorageID.IPFS_GPG]
    # job.storage_ids = [StorageID.IPFS_GPG, StorageID.IPFS]

    main_storage_id = job.storage_ids[0]
    job.cache_types = [CacheType.PUBLIC, CacheType.PUBLIC]

    # TODO: let user directly provide the IPFS hash instead of the folder
    folders = []  # full paths are provided
    folders.append(f"{env.EBLOCPATH}/base/sourceCode")
    folders.append(f"{env.EBLOCPATH}/base/data/data1")

    path_to = f"{env.EBLOCPATH}/base/data_link"
    check_linked_data(None, path_to, folders[1:], force_continue=True)
    for folder in folders:
        if not os.path.isdir(folder):
            print(f"{folder} path does not exist")
            sys.exit(1)

    if main_storage_id == StorageID.IPFS:
        log("==> Submitting source code through IPFS", "cyan")
    elif main_storage_id == StorageID.IPFS_GPG:
        log("==> Submitting source code through IPFS_GPG", "cyan")
    else:
        log("E: Please provide IPFS or IPFS_GPG storage type", "red")
        sys.exit(1)

    targets = []
    for idx, folder in enumerate(folders):
        try:
            provider_info = Ebb.get_provider_info(provider)
        except:
            sys.exit()

        target = folder
        if job.storage_ids[idx] == StorageID.IPFS_GPG:
            provider_gpg_finderprint = provider_info["gpg_fingerprint"]
            if not provider_gpg_finderprint:
                printc("E: Provider did not register any GPG fingerprint.")
                sys.exit(1)

            try:
                # target is updated
                target = gpg_encrypt(provider_gpg_finderprint, target)
                printc(f"GPG_file: {target}", "blue")
            except:
                sys.exit(1)

        try:
            ipfs_hash = ipfs.add(target)
            # ipfs_hash = ipfs.add(folder, True)  # True includes .git/
            run(["ipfs", "refs", ipfs_hash])
        except:
            _colorize_traceback()
            sys.exit(1)

        if idx == 0:
            key = ipfs_hash

        job.source_code_hashes.append(ipfs_to_bytes32(ipfs_hash))
        printc(f"ipfs_hash: {ipfs_hash}\nmd5sum: {generate_md5sum(target)}", "yellow")
        if main_storage_id == StorageID.IPFS_GPG:
            # created .gpg file will be removed since its already in ipfs
            targets.append(target)

        if idx != len(folders) - 1:
            print("--------------")

    # requester inputs for testing
    job.cores = [1]
    job.execution_durations = [1]
    job.storage_hours = [1, 1]
    job.dataTransferIns = [1, 1]  # TODO: calculate from the file itself
    job.dataTransferOut = 1
    job.data_prices_set_block_numbers = [0, 0]

    requester = Ebb.account_id_to_address(account_id)
    job_price, _cost = cost(provider, requester, job, eBlocBroker, w3)
    try:
        receipt = get_tx_status(Ebb.submit_job(provider, key, account_id, job_price, job))
        if receipt["status"] == 1:
            try:
                logs = eBlocBroker.events.LogJob().processReceipt(receipt)
                print(f"job_index={logs[0].args['index']}")
                for target in targets:
                    silent_remove(target)
            except IndexError:
                logging.error("E: Transaction is reverted.")
    except:
        _colorize_traceback()
        sys.exit(1)
    finally:
        pass
