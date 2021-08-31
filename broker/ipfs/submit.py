#!/usr/bin/env python3

import os
import sys
from pprint import pprint

from web3.logs import DISCARD

import broker.cfg as cfg
import broker.eblocbroker.Contract as Contract
from broker._utils.tools import QuietExit
from broker.config import env, logging
from broker.eblocbroker.job import Job
from broker.lib import check_linked_data, get_tx_status, run
from broker.utils import (
    CacheType,
    StorageID,
    _colorize_traceback,
    generate_md5sum,
    ipfs_to_bytes32,
    is_bin_installed,
    is_dpkg_installed,
    log,
    silent_remove,
)


def pre_check():
    """Pre check jobs to submit."""
    try:
        is_bin_installed("ipfs")
        if not is_dpkg_installed("pigz"):
            log("E: Install pigz:\nsudo apt-get install -y pigz")
            sys.exit()
    except Exception as e:
        print(str(e))
        sys.exit()


if __name__ == "__main__":
    Ebb = Contract.eblocbroker = Contract.Contract()
    job = Job()
    pre_check()
    # provider = w3.toChecksumAddress("0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49")  # netlab
    # requester_addr = w3.toChecksumAddress("0x12ba09353d5c8af8cb362d6ff1d782c1e195b571")
    provider = Ebb.w3.toChecksumAddress("0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49")
    requester_addr = Ebb.w3.toChecksumAddress("0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49")
    try:
        job.check_account_status(requester_addr)
    except Exception as e:
        _colorize_traceback(e)
        raise e

    log("==> Attemptting to submit a job")
    requester = "0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49"
    # Ebb.account_id_to_address(address=requester_addr)
    # job.storage_ids = [StorageID.IPFS_GPG, StorageID.IPFS]
    # job.storage_ids = [StorageID.IPFS_GPG, StorageID.IPFS_GPG]
    job.storage_ids = [StorageID.IPFS, StorageID.IPFS]
    _types = [CacheType.PUBLIC, CacheType.PUBLIC]
    main_storage_id = job.storage_ids[0]
    job.set_cache_types(_types)

    # TODO: let user directly provide the IPFS hash instead of the folder
    folders = []  # full paths are provided
    folders.append(f"{env.BASE_DATA_PATH}/test_data/base/source_code")
    folders.append(f"{env.BASE_DATA_PATH}/test_data/base/data/data1")
    path_from = f"{env.EBLOCPATH}/base/data"
    path_to = f"{env.LINKS}/base/data_link"
    check_linked_data(path_from, path_to, folders[1:])
    for folder in folders:
        if not os.path.isdir(folder):
            log(f"E: {folder} path does not exist")
            sys.exit(1)

    if main_storage_id == StorageID.IPFS:
        log("==> Submitting source code through IPFS")
    elif main_storage_id == StorageID.IPFS_GPG:
        log("==> Submitting source code through IPFS_GPG")
    else:
        log("E: Please provide IPFS or IPFS_GPG storage type")
        sys.exit(1)

    targets = []
    for idx, folder in enumerate(folders):
        try:
            provider_info = Ebb.get_provider_info(provider)
        except:
            sys.exit()

        target = folder
        if job.storage_ids[idx] == StorageID.IPFS_GPG:
            provider_gpg_finderprint = "11FBA2D03D3CFED18FC71D033B127BC747AADC1C"  # provider_info["gpg_fingerprint"]
            if not provider_gpg_finderprint:
                log("E: Provider did not register any GPG fingerprint")
                sys.exit(1)

            try:
                # target is updated
                target = cfg.ipfs.gpg_encrypt(provider_gpg_finderprint, target)
                log(f"==> GPG_file={target}")
            except:
                sys.exit(1)

        try:
            ipfs_hash = cfg.ipfs.add(target)
            # ipfs_hash = ipfs.add(folder, True)  # True includes .git/
            run(["ipfs", "refs", ipfs_hash])  # TODO use ipfs python
        except:
            _colorize_traceback()
            sys.exit(1)

        if idx == 0:
            key = ipfs_hash

        job.source_code_hashes_str.append(ipfs_hash)
        job.source_code_hashes.append(ipfs_to_bytes32(ipfs_hash))
        log(f"==> ipfs_hash: {ipfs_hash}\nmd5sum: {generate_md5sum(target)}", "yellow")
        if main_storage_id == StorageID.IPFS_GPG:
            # created .gpg file will be removed since its already in ipfs
            targets.append(target)

        if idx != len(folders) - 1:
            log("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-", "cyan")

    # Requester inputs for testing purpose
    job.cores = [1]
    job.run_time = [1]
    job.storage_hours = [1, 1]
    job.data_transfer_ins = [1, 1]  # TODO: calculate from the file itself
    job.dataTransferOut = 1
    job.data_prices_set_block_numbers = [0, 0]
    job_price, _cost = job.cost(provider, requester)
    try:
        tx_hash = Ebb.submit_job(provider, key, 105, job, requester=requester_addr)
        tx_receipt = get_tx_status(tx_hash)
        if tx_receipt["status"] == 1:
            processed_logs = Ebb._eBlocBroker.events.LogJob().processReceipt(tx_receipt, errors=DISCARD)
            pprint(vars(processed_logs[0].args))
            try:
                log(f"job_index={processed_logs[0].args['index']}")
                log("SUCCESS")
                for target in targets:
                    silent_remove(target)
            except IndexError:
                logging.error("E: Transaction is reverted")
    except QuietExit:
        sys.exit(1)
    except Exception as e:
        _colorize_traceback(e)
        sys.exit(1)
    finally:
        pass
