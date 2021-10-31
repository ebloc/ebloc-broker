#!/usr/bin/env python3

import sys
from pprint import pprint

from web3.logs import DISCARD

import broker.cfg as cfg
from broker._utils._log import ok
from broker._utils.tools import QuietExit
from broker.config import env
from broker.eblocbroker.job import Job
from broker.lib import check_linked_data, get_tx_status, run
from broker.submit_base import SubmitBase
from broker.utils import (
    CacheType,
    StorageID,
    _remove,
    generate_md5sum,
    ipfs_to_bytes32,
    is_bin_installed,
    is_dpkg_installed,
    log,
    print_tb,
)


def pre_check():
    """Pre check jobs to submit."""
    try:
        is_bin_installed("ipfs")
        if not is_dpkg_installed("pigz"):
            log("E: Install [green]pigz[/green].\nsudo apt install -y pigz")
            sys.exit()
    except Exception as e:
        print_tb(e)
        sys.exit()


def main():
    Ebb = cfg.Ebb
    submit_base = SubmitBase()
    job = Job()
    pre_check()
    # cfg.ipfs.connect(force=True)
    # provider = w3.toChecksumAddress("0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49")  # netlab
    # requester_addr = w3.toChecksumAddress("0x12ba09353d5c8af8cb362d6ff1d782c1e195b571")
    requester = Ebb.w3.toChecksumAddress("0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49")
    provider = Ebb.w3.toChecksumAddress("0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49")
    try:
        job.check_account_status(requester)
    except Exception as e:
        print_tb(e)
        raise e

    log("==> Attemptting to submit a job")
    # Ebb.account_id_to_address(address=requester_addr)
    # job.storage_ids = [StorageID.IPFS_GPG, StorageID.IPFS]
    job.storage_ids = [StorageID.IPFS_GPG, StorageID.IPFS_GPG]
    # job.storage_ids = [StorageID.IPFS, StorageID.IPFS]  #: works
    _types = [CacheType.PUBLIC, CacheType.PUBLIC]
    main_storage_id = job.storage_ids[0]
    job.set_cache_types(_types)

    # TODO: let user directly provide the IPFS hash instead of the folder
    #: full paths are provided
    folders_to_share = []
    folders_to_share.append(env.BASE_DATA_PATH / "test_data" / "base" / "source_code")
    folders_to_share.append(env.BASE_DATA_PATH / "test_data" / "base" / "data" / "data1")
    submit_base.check_link_folders(folders_to_share)
    if main_storage_id == StorageID.IPFS:
        log("==> Submitting source code through IPFS")
    elif main_storage_id == StorageID.IPFS_GPG:
        log("==> Submitting source code through IPFS_GPG")
    else:
        log("E: Please provide IPFS or IPFS_GPG storage type for the source code")
        sys.exit(1)

    targets = []
    for idx, folder in enumerate(folders_to_share):
        try:
            provider_info = Ebb.get_provider_info(provider)
        except Exception as e:
            print_tb(e)
            sys.exit(1)

        target = folder
        if job.storage_ids[idx] == StorageID.IPFS_GPG:
            provider_gpg_finderprint = provider_info["gpg_fingerprint"]
            if not provider_gpg_finderprint:
                log("E: Provider did not register any GPG fingerprint")
                sys.exit(1)

            log(f"==> provider_gpg_finderprint={provider_gpg_finderprint}")
            try:
                # target is updated
                target = cfg.ipfs.gpg_encrypt(provider_gpg_finderprint, target)
                log(f"==> gpg_file={target}")
            except Exception as e:
                print_tb(e)
                sys.exit(1)

        try:
            ipfs_hash = cfg.ipfs.add(target)
            # ipfs_hash = ipfs.add(folder, True)  # True includes .git/
            run(["ipfs", "refs", ipfs_hash])  # TODO use ipfs python
        except Exception as e:
            print_tb(e)
            sys.exit(1)

        if idx == 0:
            key = ipfs_hash

        job.source_code_hashes_str.append(ipfs_hash)
        job.source_code_hashes.append(ipfs_to_bytes32(ipfs_hash))
        log(f"==> ipfs_hash={ipfs_hash}")
        log(f"==> md5sum={generate_md5sum(target)}")
        if main_storage_id == StorageID.IPFS_GPG:
            # created gpg file will be removed since its already in ipfs
            targets.append(target)

        if idx != len(folders_to_share) - 1:
            log("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-", "cyan")

    # Requester inputs for testing purpose
    job.cores = [1]
    job.run_time = [1]
    job.storage_hours = [1, 1]
    job.data_transfer_ins = [1, 1]  # TODO: calculate from the file itself
    job.data_transfer_out = 1
    job.data_prices_set_block_numbers = [0, 0]
    job_price, cost = job.cost(provider, requester)
    try:
        tx_hash = Ebb.submit_job(provider, key, job_price, job, requester=requester)
        tx_receipt = get_tx_status(tx_hash)
        if tx_receipt["status"] == 1:
            processed_logs = Ebb._eBlocBroker.events.LogJob().processReceipt(tx_receipt, errors=DISCARD)
            pprint(vars(processed_logs[0].args))
            try:
                log(f"{ok()} [bold]job_index={processed_logs[0].args['index']}")
                for target in targets:
                    _remove(target)
            except IndexError:
                log(f"E: Tx({tx_hash}) is reverted")
    except QuietExit:
        pass
    except Exception as e:
        print_tb(e)


if __name__ == "__main__":
    main()
