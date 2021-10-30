#!/usr/bin/env python3

import broker.cfg as cfg
import broker.libs.gdrive as gdrive
import broker.libs.git as git
from broker.config import env
from broker.eblocbroker.job import Job
from broker.lib import check_linked_data
from broker.utils import CacheType, StorageID, is_program_valid, log, print_tb


Ebb = cfg.Ebb
# TODO: if a-source submitted with b-data and b-data is updated meta_data.json
# file remain with the previos sent version


def main():
    job = Job()
    is_program_valid(["gdrive", "version"])

    job.base_dir = f"{env.EBLOCPATH}/base"
    job.folders_to_share.append(f"{job.base_dir}/source_code")
    job.folders_to_share.append(f"{job.base_dir}/data/data1")

    path_from = env.EBLOCPATH / "base" / "data"
    path_to = env.LINK_PATH / "base" / "data_link"
    check_linked_data(path_from, path_to, job.folders_to_share[1:])

    # IMPORTANT: consider ignoring to push .git into the submitted folder
    git.generate_git_repo(job.folders_to_share)
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
    job.cache_types = [CacheType.PRIVATE, CacheType.PUBLIC]
    job.storage_hours = [1, 1]
    job.data_prices_set_block_numbers = [0, 0]
    for folder_to_share in job.folders_to_share:
        tar_hash = job.foldername_tar_hash[folder_to_share]
        # required to send string as bytes == str_data.encode('utf-8')
        job.source_code_hashes.append(Ebb.w3.toBytes(text=tar_hash))

    tar_hash = job.foldername_tar_hash[job.folders_to_share[0]]
    job_key = job.keys[tar_hash]
    try:
        job_price, _cost = job.cost(provider, _from, job)
        tx_hash = Ebb.submit_job(provider, job_key, job_price, job, requester=_from)
    except Exception as e:
        raise e

    for k, v in job.tar_hashes.items():
        log(f"{k} => {v}")

    log(f"==> source_code_hashes={job.source_code_hashes}")
    if job.analyze_tx_status(tx_hash):
        log("SUCCESS")
    else:
        log("FAILED")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print_tb(e)
