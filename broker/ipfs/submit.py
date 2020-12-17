#!/usr/bin/env python3

import os
import sys

from web3.logs import DISCARD

from broker import cfg
from broker._utils._log import ok
from broker.config import env
from broker.eblocbroker.job import Job
from broker.errors import QuietExit
from broker.lib import get_tx_status, run
from broker.submit_base import SubmitBase
from broker.utils import (
    StorageID,
    _remove,
    generate_md5sum,
    ipfs_to_bytes32,
    is_bin_installed,
    is_dpkg_installed,
    log,
    print_tb,
    run_ipfs_daemon,
)

# TODO: folders_to_share let user directly provide the IPFS hash instead of the folder


def pre_check():
    """Pre check jobs to submit."""
    try:
        is_bin_installed("ipfs")
        if not is_dpkg_installed("pigz"):
            log("E: Install [green]pigz[/green].\nsudo apt install -y pigz")
            sys.exit()

        if not os.path.isfile(env.GPG_PASS_FILE):
            log(f"E: Please store your gpg password in the [magenta]{env.GPG_PASS_FILE}[/magenta]\nfile for decrypting")
            raise QuietExit

        run_ipfs_daemon()
    except Exception as e:
        print_tb(e)
        sys.exit()


def submit_ipfs(job_config_fn):
    pre_check()
    Ebb = cfg.Ebb
    submit_base = SubmitBase()
    job = Job()
    job.set_config(job_config_fn)
    requester = Ebb.w3.toChecksumAddress("0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49")
    provider = Ebb.w3.toChecksumAddress(job.provider_addr)
    try:
        job.check_account_status(requester)
    except Exception as e:
        print_tb(e)
        raise e

    log("==> Attemptting to submit a job")
    if job.storage_ids[0] == StorageID.IPFS:
        for storage_id in job.storage_ids[1:]:
            if storage_id in (StorageID.GDRIVE, StorageID.EUDAT):
                raise Exception(
                    "If source code is submitted via IPFS, data files should be submitted via IPFS or IPFS_GPG"
                )

    main_storage_id = job.storage_ids[0]
    job.folders_to_share = job.paths
    submit_base.check_link_folders(job.folders_to_share)
    if main_storage_id == StorageID.IPFS:
        log("==> Submitting source code through IPFS")
    elif main_storage_id == StorageID.IPFS_GPG:
        log("==> Submitting source code through IPFS_GPG")
    else:
        log("E: Please provide IPFS or IPFS_GPG storage type for the source code")
        sys.exit(1)

    targets = []
    for idx, folder in enumerate(job.folders_to_share):
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
            run(["ipfs", "refs", ipfs_hash])
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

        if idx != len(job.folders_to_share) - 1:
            log("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-", "cyan")

    # Requester inputs for testing purpose
    job.price, *_ = job.cost(provider, requester)
    try:
        tx_hash = Ebb.submit_job(provider, key, job, requester=requester)
        tx_receipt = get_tx_status(tx_hash)
        if tx_receipt["status"] == 1:
            processed_logs = Ebb._eBlocBroker.events.LogJob().processReceipt(tx_receipt, errors=DISCARD)
            log(vars(processed_logs[0].args))
            try:
                log(f"{ok()} [bold]job_index={processed_logs[0].args['index']}")
                for target in targets:
                    if ".tar.gz.gpg" in target:
                        _remove(target)
            except IndexError:
                log(f"E: Tx({tx_hash}) is reverted")
    except QuietExit:
        pass
    except Exception as e:
        print_tb(e)


if __name__ == "__main__":
    submit_ipfs("/home/alper/ebloc-broker/broker/ipfs/job_simple.yaml")
