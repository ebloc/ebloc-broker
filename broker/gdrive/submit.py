#!/usr/bin/env python3

import sys

from web3.logs import DISCARD

from broker import cfg
from broker._utils._log import ok
from broker._utils.web3_tools import get_tx_status
from broker.eblocbroker_scripts.job import Job
from broker.errors import QuietExit
from broker.lib import run
from broker.libs import _git, gdrive
from broker.link import check_link_folders
from broker.utils import is_program_valid, log, print_tb

# TODO: if a-source submitted with b-data and b-data is updated meta_data.json
# file remain with the previos sent version

Ebb = cfg.Ebb


def pre_check():
    is_program_valid(["gdrive", "version"])
    try:
        run(["gdrive", "about"])
    except Exception as e:
        print_tb(e)
        raise QuietExit from e


def submit_gdrive(job: Job, is_pass=False, required_confs=1):
    log("==> Submitting source code through [blue]GDRIVE[/blue]")
    pre_check()
    job.folders_to_share = job.paths
    check_link_folders(job.data_paths, job.registered_data_files, is_pass=is_pass)
    _git.generate_git_repo(job.folders_to_share)
    job.clean_before_submit()
    requester = Ebb.w3.toChecksumAddress(job.requester_addr)
    provider = Ebb.w3.toChecksumAddress(job.provider_addr)
    job = gdrive.submit(provider, requester, job)
    for folder_to_share in job.folders_to_share:
        if isinstance(folder_to_share, bytes):
            code_hash = folder_to_share
            job.code_hashes.append(code_hash)
            job.code_hashes_str.append(code_hash.decode("utf-8"))
        else:
            tar_hash = job.foldername_tar_hash[folder_to_share]
            #: required to send string as bytes == str_data.encode('utf-8')
            code_hash = Ebb.w3.toBytes(text=tar_hash)
            job.code_hashes.append(code_hash)
            job.code_hashes_str.append(code_hash.decode("utf-8"))

    tar_hash = job.foldername_tar_hash[job.folders_to_share[0]]
    key = job.keys[tar_hash]
    job.price, *_ = job.cost(provider, requester)
    try:
        tx_hash = Ebb.submit_job(provider, key, job, requester=requester, required_confs=required_confs)
        tx_receipt = get_tx_status(tx_hash)
        if tx_receipt["status"] == 1:
            processed_logs = Ebb._eblocbroker.events.LogJob().processReceipt(tx_receipt, errors=DISCARD)
            log(vars(processed_logs[0].args))
            try:
                log(f"[bold]job_index={processed_logs[0].args['index']}{ok()}")
            except IndexError:
                log(f"E: Tx({tx_hash}) is reverted")
    # except QuietExit:
    #     pass
    except Exception as e:
        print_tb(e)

    log()
    for k, v in job.tar_hashes.items():
        log(f"{k} [blue]=>[/blue] {v}")

    return tx_hash


if __name__ == "__main__":
    try:
        job = Job()
        # fn = "job_with_data.yaml"
        fn = "job.yaml"
        job.set_config(fn)
        submit_gdrive(job)
    # except QuietExit:
    #     sys.exit(1)
    # except KeyboardInterrupt:
    #     sys.exit(1)
    except Exception as e:
        print_tb(e)
