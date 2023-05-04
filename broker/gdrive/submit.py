#!/usr/bin/env python3

from web3.logs import DISCARD

from broker import cfg
from broker._utils._log import log, ok
from broker._utils.web3_tools import get_tx_status
from broker.eblocbroker_scripts.job import Job
from broker.errors import QuietExit
from broker.lib import run
from broker.libs import _git, gdrive
from broker.libs.gdrive import check_gdrive
from broker.link import check_link_folders
from broker.utils import print_tb

# TODO: if a-source submitted with b-data and b-data is updated meta_data.json
# file remain with the previos sent version

Ebb = cfg.Ebb


def pre_check():
    check_gdrive()


def _submit(job, provider, key, requester, required_confs):
    try:
        tx_hash = Ebb.submit_job(provider, key, job, requester=requester, required_confs=required_confs)
        tx_receipt = get_tx_status(tx_hash)
        if tx_receipt["status"] == 1:
            processed_logs = Ebb._eblocbroker.events.LogJob().processReceipt(tx_receipt, errors=DISCARD)
            log(vars(processed_logs[0].args))
            try:
                log(f"job_index={processed_logs[0].args['index']} {ok()}")
            except IndexError:
                log(f"E: Tx({tx_hash}) is reverted")
    except Exception as e:
        print_tb(e)

    log()
    for k, v in job.tar_hashes.items():
        log(f"{k} [blue]=>[/blue] {v}")

    return tx_hash


def _share_folders(folder_ids_to_share, provider_gmail):
    for folder_id in folder_ids_to_share:
        cmd = ["gdrive", "share", folder_id, "--role", "writer", "--type", "user", "--email", provider_gmail]
        log(f"share_output=[m]{run(cmd)}")


def submit_gdrive(job: Job, is_pass=False, required_confs=1):
    log("==> Submitting source code through [blue]GDRIVE[/blue]")
    requester = Ebb.w3.toChecksumAddress(job.requester_addr)
    Ebb._pre_check(requester)
    pre_check()
    job.folders_to_share = job.paths
    check_link_folders(job.data_paths, job.registered_data_files, job.source_code_path, is_pass=is_pass)
    _git.generate_git_repo(job.folders_to_share)
    job.clean_before_submit()
    job, folder_ids_to_share = gdrive.submit(requester, job)
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
    provider_addr_to_submit = job.search_best_provider(requester)
    try:
        job.Ebb.is_provider_valid(provider_addr_to_submit)
        provider_info = job.Ebb.get_provider_info(provider_addr_to_submit)
        provider_gmail = provider_info["gmail"]
    except Exception as e:
        raise QuietExit from e

    _share_folders(folder_ids_to_share, provider_gmail)
    return _submit(job, provider_addr_to_submit, key, requester, required_confs)


if __name__ == "__main__":
    try:
        job = Job()
        # fn = "job_with_data.yaml"
        fn = "job.yaml"
        job.set_config(fn)
        submit_gdrive(job)
    except Exception as e:
        print_tb(e)
