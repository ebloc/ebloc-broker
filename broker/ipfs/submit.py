#!/usr/bin/env python3

import os
import sys
from pathlib import Path

from web3.logs import DISCARD

from broker import cfg
from broker._utils.tools import _remove, log
from broker._utils.web3_tools import get_tx_status
from broker.config import env
from broker.eblocbroker_scripts.job import Job
from broker.errors import QuietExit
from broker.lib import run
from broker.link import check_link_folders
from broker.utils import (
    StorageID,
    generate_md5sum,
    ipfs_to_bytes32,
    is_bin_installed,
    is_dpkg_installed,
    print_tb,
    start_ipfs_daemon,
)

# TODO: folders_to_share let user directly provide the IPFS hash instead of the folder
ipfs = cfg.ipfs
Ebb = cfg.Ebb


def pre_check_gpg(requester):
    requester_info = Ebb.get_requester_info(requester)
    from_gpg_fingerprint = ipfs.get_gpg_fingerprint(env.GMAIL).upper()
    if requester_info["gpg_fingerprint"].upper() != from_gpg_fingerprint:
        raise Exception(
            f"E: requester({requester})'s gpg_fingerprint({requester_info['gpg_fingerprint'].upper()}) does not "
            f"match with registered gpg_fingerprint={from_gpg_fingerprint}"
        )

    try:
        ipfs.is_gpg_published(from_gpg_fingerprint)
    except Exception as e:
        raise e


def pre_check(job: Job, requester):
    """Pre check jobs to submit."""
    try:
        for storage_id in job.storage_ids:
            if storage_id == StorageID.IPFS_GPG:
                pre_check_gpg(requester)
                break

        job.check_account_status(requester)
        is_bin_installed("ipfs")
        if not is_dpkg_installed("pigz"):
            log("E: Install [green]pigz[/green].\nsudo apt install -y pigz")
            sys.exit()

        if not os.path.isfile(env.GPG_PASS_FILE):
            log(f"E: Please store your gpg password in the [magenta]{env.GPG_PASS_FILE}[/magenta]\nfile for decrypting")
            raise QuietExit

        start_ipfs_daemon()
        if job.storage_ids[0] == StorageID.IPFS:
            for storage_id in job.storage_ids[1:]:
                if storage_id in (StorageID.GDRIVE, StorageID.EUDAT):
                    raise Exception(
                        "If source code is submitted via IPFS, then data files must be submitted using IPFS or IPFS_GPG"
                    )
    except Exception as e:
        print_tb(e)
        sys.exit()


def _ipfs_add(job, target, idx, is_verbose=False):
    try:
        ipfs_hash = ipfs.add(target)
        # ipfs_hash = ipfs.add(folder, True)  # True includes .git/
        run(["ipfs", "refs", ipfs_hash])
    except Exception as e:
        print_tb(e)
        sys.exit(1)

    if idx == 0:
        job.key = ipfs_hash

    job.code_hashes.append(ipfs_to_bytes32(ipfs_hash))
    job.code_hashes_str.append(ipfs_hash)
    if not is_verbose:
        log(f"==> ipfs_hash={ipfs_hash} | md5sum={generate_md5sum(target)}")

    return job


def submit_ipfs(job: Job, is_pass=False, required_confs=1):
    requester = Ebb.w3.toChecksumAddress(job.requester_addr)
    provider = Ebb.w3.toChecksumAddress(job.provider_addr)
    pre_check(job, requester)
    log(f"==> Attemptting to submit job ({job.source_code_path})")
    main_storage_id = job.storage_ids[0]
    job.folders_to_share = job.paths
    check_link_folders(job.data_paths, job.registered_data_files, job.source_code_path, is_pass=is_pass)
    if main_storage_id == StorageID.IPFS:
        log("==> Submitting source code through [blue]IPFS[/blue]")
    elif main_storage_id == StorageID.IPFS_GPG:
        log("==> Submitting source code through [blue]IPFS_GPG[/blue]")
    else:
        log("E: Please provide IPFS or IPFS_GPG storage type for the source code")
        sys.exit(1)

    try:
        provider_info = Ebb.get_provider_info(provider)
    except Exception as e:
        print_tb(e)
        sys.exit(1)

    targets = []
    is_ipfs_gpg = False
    for idx, folder in enumerate(job.folders_to_share):
        if isinstance(folder, Path):
            target = folder
            if job.storage_ids[idx] == StorageID.IPFS_GPG:
                is_ipfs_gpg = True
                job.code_hashes.append(b"")  # dummy items added
                job.code_hashes_str.append("")  # dummy items added
            else:
                job = _ipfs_add(job, target, idx)
        else:
            code_hash = folder
            if isinstance(code_hash, bytes):
                job.code_hashes.append(code_hash)
                job.code_hashes_str.append(code_hash.decode("utf-8"))

    provider_addr_to_submit = job.search_best_provider(requester)
    if is_ipfs_gpg:  # re-organize with gpg file
        job.code_hashes = []
        job.code_hashes_str = []
        provider_info = job.Ebb.get_provider_info(provider_addr_to_submit)
        provider_gpg_fingerprint = provider_info["gpg_fingerprint"]
        if not provider_gpg_fingerprint:
            log("E: Provider did not register any GPG fingerprint")
            sys.exit(1)

        log(f"==> provider_gpg_fingerprint={provider_gpg_fingerprint}")
        for idx, folder in enumerate(job.folders_to_share):
            if isinstance(folder, Path):
                target = folder
                if job.storage_ids[idx] == StorageID.IPFS_GPG:
                    is_ipfs_gpg = True
                    try:
                        from_gpg_fingerprint = ipfs.get_gpg_fingerprint(env.GMAIL).upper()
                        #: target is updated
                        target = ipfs.gpg_encrypt(from_gpg_fingerprint, provider_gpg_fingerprint, target)
                        log(f"==> gpg_file={target}")
                        targets.append(target)  #: created gpg file will be removed since its already in ipfs
                    except Exception as e:
                        print_tb(e)
                        sys.exit(1)

                job = _ipfs_add(job, target, idx)
            else:
                code_hash = folder
                if isinstance(code_hash, bytes):
                    job.code_hashes.append(code_hash)
                    job.code_hashes_str.append(code_hash.decode("utf-8"))

        job.price, *_ = job.cost(provider_addr_to_submit, requester)

    try:
        tx_hash = Ebb.submit_job(provider_addr_to_submit, job.key, job, requester, required_confs)
        if required_confs >= 1:
            tx_receipt = get_tx_status(tx_hash)
            if tx_receipt["status"] == 1:
                processed_logs = Ebb._eblocbroker.events.LogJob().processReceipt(tx_receipt, errors=DISCARD)
                try:
                    if processed_logs:
                        log("[yellow]job_info[/yellow]=", "bold", end="")
                        log(vars(processed_logs[0].args))

                    for target in targets:
                        if ".tar.gz.gpg" in str(target):
                            _remove(target)
                except IndexError:
                    log(f"E: Tx={tx_hash} is reverted")
    except QuietExit:
        pass
    except Exception as e:
        print_tb(e)

    return tx_hash


def main():
    job = Job()
    job.set_config(Path.home() / "ebloc-broker" / "broker" / "ipfs" / "job.yaml")
    submit_ipfs(job)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception as e:
        print_tb(e)
