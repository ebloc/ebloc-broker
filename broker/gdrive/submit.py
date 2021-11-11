#!/usr/bin/env python3

from web3.logs import DISCARD

from broker import cfg
from broker._utils._log import ok
from broker._utils.tools import QuietExit
from broker.eblocbroker.job import Job
from broker.lib import get_tx_status
from broker.libs import _git, gdrive
from broker.link import check_link_folders
from broker.utils import is_program_valid, log, print_tb

# TODO: if a-source submitted with b-data and b-data is updated meta_data.json
# file remain with the previos sent version


def pre_check():
    is_program_valid(["gdrive", "version"])


def submit_gdrive(job: Job):
    pre_check()
    Ebb = cfg.Ebb
    job.folders_to_share = job.paths
    check_link_folders(job.folders_to_share)
    # IMPORTANT: consider ignoring to push .git into the submitted folder
    _git.generate_git_repo(job.folders_to_share)
    job.clean_before_submit()
    requester = Ebb.w3.toChecksumAddress("0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49")
    provider = Ebb.w3.toChecksumAddress(job.provider_addr)
    job = gdrive.submit(provider, requester, job)
    for folder_to_share in job.folders_to_share:
        tar_hash = job.foldername_tar_hash[folder_to_share]
        #: required to send string as bytes == str_data.encode('utf-8')
        value = Ebb.w3.toBytes(text=tar_hash)
        job.source_code_hashes.append(value)
        job.source_code_hashes_str.append(value.decode("utf-8"))

    tar_hash = job.foldername_tar_hash[job.folders_to_share[0]]
    key = job.keys[tar_hash]
    job.price, *_ = job.cost(provider, requester)
    try:
        tx_hash = Ebb.submit_job(provider, key, job, requester=requester)
        tx_receipt = get_tx_status(tx_hash)
        if tx_receipt["status"] == 1:
            processed_logs = Ebb._eBlocBroker.events.LogJob().processReceipt(tx_receipt, errors=DISCARD)
            log(vars(processed_logs[0].args))
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
        job = Job()
        job.set_config("/home/alper/ebloc-broker/broker/gdrive/job.yaml")
        submit_gdrive(job)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print_tb(e)
