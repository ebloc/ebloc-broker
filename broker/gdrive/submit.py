#!/usr/bin/env python3

from pprint import pprint

from web3.logs import DISCARD

from broker import cfg
from broker._utils._log import ok
from broker._utils.tools import QuietExit
from broker.config import env
from broker.eblocbroker.job import Job
from broker.lib import get_tx_status
from broker.libs import gdrive, _git
from broker.submit_base import SubmitBase
from broker.utils import CacheType, StorageID, is_program_valid, log, print_tb

# TODO: if a-source submitted with b-data and b-data is updated meta_data.json
# file remain with the previos sent version


def main():
    Ebb = cfg.Ebb
    submit_base = SubmitBase()
    job = Job()
    is_program_valid(["gdrive", "version"])
    job.base_dir = env.BASE_DATA_PATH
    job.folders_to_share.append(env.BASE_DATA_PATH / "test_data" / "base" / "source_code")
    job.folders_to_share.append(env.BASE_DATA_PATH / "test_data" / "base" / "data" / "data1")
    submit_base.check_link_folders(job.folders_to_share)
    # IMPORTANT: consider ignoring to push .git into the submitted folder
    _git.generate_git_repo(job.folders_to_share)
    job.clean_before_submit()
    requester = Ebb.w3.toChecksumAddress("0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49")
    provider = "0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49"  # home2-vm
    job = gdrive.submit(provider, requester, job)
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
        #: required to send string as bytes == str_data.encode('utf-8')
        value = Ebb.w3.toBytes(text=tar_hash)
        job.source_code_hashes.append(value)
        job.source_code_hashes_str.append(value.decode("utf-8"))

    tar_hash = job.foldername_tar_hash[job.folders_to_share[0]]
    key = job.keys[tar_hash]
    job_price, *_ = job.cost(provider, requester)
    try:
        tx_hash = Ebb.submit_job(provider, key, job_price, job, requester=requester)
        tx_receipt = get_tx_status(tx_hash)
        if tx_receipt["status"] == 1:
            processed_logs = Ebb._eBlocBroker.events.LogJob().processReceipt(tx_receipt, errors=DISCARD)
            pprint(vars(processed_logs[0].args))
            try:
                log(f"{ok()} [bold]job_index={processed_logs[0].args['index']}")
            except IndexError:
                log(f"E: Tx({tx_hash}) is reverted")
    except QuietExit:
        pass
    except Exception as e:
        print_tb(e)

    log()
    for k, v in job.tar_hashes.items():
        log(f"{k} [blue]=>[/blue] {v}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print_tb(e)
