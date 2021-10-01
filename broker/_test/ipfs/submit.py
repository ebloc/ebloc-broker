#!/usr/bin/env python3

import os
import sys
from pprint import pprint

from config import env, logging
from imports import connect
from lib import check_linked_data, get_tx_status, run
from libs import ipfs
from libs.ipfs import gpg_encrypt
from utils import CacheType, StorageID, _remove, generate_md5sum, ipfs_to_bytes32, is_dpkg_installed, log, print_tb
from web3.logs import DISCARD

import broker.eblocbroker.Contract as Contract
from broker._utils.tools import QuietExit
from contract.scripts.lib import Job, cost
import broker.cfg as cfg


if __name__ == "__main__":
    eBlocBroker, w3 = connect()
    Ebb = cfg.Ebb
    job = Job()

    if not is_dpkg_installed("pigz"):
        log("E: Install pigz:\nsudo apt-get install pigz")
        sys.exit()

    account_id = 1
    provider = w3.toChecksumAddress("0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49")  # netlab
    try:
        job.check_account_status(account_id)
    except Exception as e:
        raise e

    log("==> Attempt to submit a job")
    # job.storage_ids = [StorageID.IPFS_GPG, StorageID.IPFS]
    job.storage_ids = [StorageID.IPFS_GPG, StorageID.IPFS_GPG]
    # job.storage_ids = [StorageID.IPFS, StorageID.IPFS]
    _types = [CacheType.PUBLIC, CacheType.PUBLIC]

    main_storage_id = job.storage_ids[0]
    job.set_cache_types(_types)

    base_dir = f"{env.HOME}/_test"
    source_code_dir = os.path.join(base_dir, "source_code")
    data_1_dir = os.path.join(base_dir, "datasets/BL06-camel-sml")

    # TODO: let user directly provide the IPFS hash instead of the folder
    folders_to_share = []
    folders_to_share.append(source_code_dir)
    folders_to_share.append(data_1_dir)

    path_from = f"{env.EBLOCPATH}/base/data"
    path_to = f"{env.LINKS}/base/data_link"
    check_linked_data(path_from, path_to, folders_to_share[1:])

    if main_storage_id == StorageID.IPFS:
        log("==> Submitting source code through IPFS", "cyan")
    elif main_storage_id == StorageID.IPFS_GPG:
        log("==> Submitting source code through IPFS_GPG", "cyan")
    else:
        log("E: Please provide IPFS or IPFS_GPG storage type")
        sys.exit(1)

    targets = []
    for idx, folder in enumerate(folders_to_share):
        try:
            provider_info = Ebb.get_provider_info(provider)
        except:
            sys.exit()

        target = folder
        if job.storage_ids[idx] == StorageID.IPFS_GPG:
            provider_gpg_finderprint = provider_info["gpg_fingerprint"]
            if not provider_gpg_finderprint:
                log("E: Provider did not register any GPG fingerprint")
                sys.exit(1)

            try:
                # target is updated
                target = gpg_encrypt(provider_gpg_finderprint, target)
                log(f"==> GPG_file={target}")
            except:
                sys.exit(1)

        try:
            # TODO: check git init && git commit
            ipfs_hash = ipfs.add(target)
            # ipfs_hash = ipfs.add(folder, is_hidden=True)  # True includes .git/, which changes the overall ipfs-hash
            run(["ipfs", "refs", ipfs_hash])
        except:
            print_tb()
            sys.exit(1)

        if idx == 0:
            key = ipfs_hash

        job.source_code_hashes.append(ipfs_to_bytes32(ipfs_hash))
        log(f"==> ipfs_hash: {ipfs_hash}")
        log(f"==> md5sum: {generate_md5sum(target)}")
        if main_storage_id == StorageID.IPFS_GPG:
            # created .gpg file will be removed since its already in ipfs
            targets.append(target)

        if idx != len(folders_to_share) - 1:
            log("-------------------------------------------------", "yellow")

    # requester inputs for testing
    job.cores = [1]
    job.run_time = [1]
    job.storage_hours = [1, 1]
    job.data_transfer_in = [1, 1]  # TODO: calculate from the file itself
    job.dataTransferOut = 1
    job.data_prices_set_block_numbers = [0, 0]

    requester = Ebb.account_id_to_address(account_id)
    job_price, _cost = cost(provider, requester, job)
    try:
        tx_receipt = get_tx_status(Ebb.submit_job(provider, key, account_id, job_price, job))
        if tx_receipt["status"] == 1:
            processed_logs = eBlocBroker.events.LogJob().processReceipt(tx_receipt, errors=DISCARD)
            pprint(vars(processed_logs[0].args))
            try:
                log(f"job_index={processed_logs[0].args['index']}")
                log("SUCCESS")
                for target in targets:
                    _remove(target)
            except IndexError:
                logging.error("E: Transaction is reverted")
    except QuietExit:
        sys.exit(1)
    except:
        print_tb()
        sys.exit(1)
    finally:
        pass
