#!/usr/bin/env python3

import sys

from broker import cfg
from broker.config import env
from broker.eblocbroker_scripts.job import Job
from broker.libs import gdrive
from broker.link import check_linked_data
from broker.utils import CacheID, StorageID, log, print_tb

# TODO: if a-source submitted with b-data and b-data is updated meta_data.json
# file remain with the previos sent version


def main():
    job = Job()
    Ebb = cfg.Ebb
    job.base_dir = f"{env.HOME}/test_eblocbroker"
    job.source_code_dir = f"{job.base_dir}/source_code"
    job.data_1_dir = f"{job.base_dir}/datasets/BL06-camel-sml"

    job.folders_to_share.append(job.source_code_dir)
    job.folders_to_share.append(job.data_1_dir)

    path_from = f"{job.base_dir}/datasets"
    path_to = f"{env.LINK_PATH}/base/data_link"
    check_linked_data(path_from, path_to, job.folders_to_share[1:])

    # IMPORTANT: consider ignoring to push .git into the submitted folder
    # job.generate_git_repos()
    job.clean_before_submit()

    provider = "0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49"  # home2-vm
    account_id = 1
    _from = Ebb.w3.toChecksumAddress(Ebb.w3.eth.accounts[account_id])
    job = gdrive.submit(provider, _from, job)
    job.run_time = [5]
    job.cores = [1]
    job.data_transfer_ins = [1, 1]
    job.data_transfer_out = 1

    job.storage_ids = [StorageID.GDRIVE, StorageID.GDRIVE]
    job.cache_types = [CacheID.PRIVATE, CacheID.PUBLIC]
    job.storage_hours = [1, 1]
    job.data_prices_set_block_numbers = [0, 0]

    for folder_to_share in job.folders_to_share:
        tar_hash = job.foldername_tar_hash[folder_to_share]
        # required to send string as bytes == str_data.encode('utf-8')
        job.code_hashes.append(Ebb.w3.toBytes(text=tar_hash))

    tar_hash = job.foldername_tar_hash[job.folders_to_share[0]]
    job_key = job.keys[tar_hash]
    try:
        job_price, _cost = job.cost(provider, _from)
        tx_hash = Ebb.submit_job(provider, job_key, job_price, job, requester=_from)
    except Exception as e:
        raise e

    for k, v in job.tar_hashes.items():
        log(f"{k} => {v}")

    log(f"==> code_hashes={job.code_hashes}")
    if job.analyze_tx_status(tx_hash):
        log("SUCCESS")
    else:
        log("FAILED")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        if type(e).__name__ != "KeyboardInterrupt":
            print_tb()
        sys.exit(1)
