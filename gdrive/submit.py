#!/usr/bin/env python3

import json
import os
import shutil
import sys
from pprint import pprint

from web3.logs import DISCARD

import eblocbroker.Contract as Contract
import libs.gdrive as gdrive
import libs.git as git
from config import QuietExit, env, logging
from contract.scripts.lib import Job, cost
from lib import get_tx_status, run
from utils import CacheType, StorageID, _colorize_traceback, compress_folder, log, mkdir, read_json, silent_remove

base_folder = f"{env.EBLOCPATH}/base"
Ebb = Contract.eblocbroker
tar_hashes = {}


def create_meta_json(filename, job_keys):
    with open(filename, "w") as f:
        json.dump(job_keys, f)
    log("==> meta_data.json file is updated into the parent folder")


def gdrive_upload(folder_to_share, job_key_flag=False):
    is_already_uploaded = False
    log(f"==> job_key_flag={job_key_flag}, tar.gz file is inside a folder")
    dir_path = os.path.dirname(folder_to_share)
    tar_hash, _ = compress_folder(folder_to_share)
    breakpoint()  # DEBUG
    tar_hashes[folder_to_share] = tar_hash

    path_to_move = f"{dir_path}/{tar_hash}"
    _from = f"{dir_path}/{tar_hash}.tar.gz"
    _to = f"{path_to_move}/{tar_hash}.tar.gz"

    mkdir(path_to_move)
    shutil.move(_from, _to)
    if job_key_flag:
        shutil.copyfile(f"{base_folder}/meta_data.json", f"{path_to_move}/meta_data.json")

    is_file_exist = gdrive._list(tar_hash, is_folder=True)
    if not is_file_exist:
        key = gdrive._upload(dir_path, tar_hash, is_folder=True)
        logging.info(gdrive._list(tar_hash))
    else:
        log(f"==> Requested folder {tar_hash} is already uploaded", color="blue")
        logging.info(is_file_exist)
        key = is_file_exist.partition("\n")[0].split()[0]
        is_already_uploaded = True

    silent_remove(f"{dir_path}/{tar_hash}")  # created .tar.gz file is removed
    return key, is_already_uploaded, tar_hash


def share_folder(folder_to_share, provider_to_share, job_key_flag=False):
    logging.info(f"folder_to_share={folder_to_share}")
    key, is_already_uploaded, tar_hash = gdrive_upload(folder_to_share, job_key_flag)
    cmd = ["gdrive", "share", key, "--role", "writer", "--type", "user", "--email", provider_to_share]
    if not is_already_uploaded:
        log(f"share_output={run(cmd)}")
    return key, tar_hash


def gdrive_submit_job(provider, _from):
    job = Job()
    try:
        job.check_account_status(_from)
    except Exception as e:
        raise e

    try:
        provider_info = Ebb.get_provider_info(provider)
        print(f"Provider's available_core_num={provider_info['available_core_num']}")
        print(f"Provider's price_core_min={provider_info['price_core_min']}")
    except:
        raise QuietExit

    Ebb.is_provider_valid(provider)
    Ebb.is_requester_valid(_from)
    provider = Ebb.w3.toChecksumAddress(provider)
    provider_to_share = provider_info["email"]

    job_keys = {}
    foldername_tar_hash = {}
    job.folders_to_share.append(f"{base_folder}/sourceCode")
    job.folders_to_share.append(f"{base_folder}/data/data1")
    # subprocess.run(['sudo', 'chmod', '-R', '777', folder_to_share])

    # IMPORTANT: consider ignoring to push .git into the submitted folder
    # for folder in job.folders_to_share:
    #     log(folder, color="green")
    #     try:
    #         git.initialize_check(folder)
    #         git.commit_changes(folder)
    #     except:
    #         sys.exit(1)

    try:
        if len(job.folders_to_share) > 1:
            for folder_to_share in job.folders_to_share[1:]:
                # starting from the first element ignoring source_folder
                # attempting to share the data folder
                job_key, tar_hash = share_folder(folder_to_share, provider_to_share)
                foldername_tar_hash[folder_to_share] = tar_hash
                job_keys[tar_hash] = job_key

            data_files_json_path = f"{base_folder}/meta_data.json"
            try:
                data_json = read_json(data_files_json_path)
                if job_keys == data_json:
                    log("## meta_data.json file matches with the given data keys", color="green")
                else:
                    log("## meta_data.json file does not match with the given data keys", color="blue")
                    create_meta_json(f"{base_folder}/meta_data.json", job_keys)
                    data_json = read_json(data_files_json_path)
            except:
                create_meta_json(f"{base_folder}/meta_data.json", job_keys)
                data_json = read_json(data_files_json_path)

            log("meta_data:-------------------------------------------------------", color="blue")
            pprint(str(data_json))
            log("-----------------------------------------------------------------", color="blue")

        folder_to_share = job.folders_to_share[0]
        job_key, tar_hash = share_folder(folder_to_share, provider_to_share, job_key_flag=True)
        foldername_tar_hash[folder_to_share] = tar_hash
        job_keys[tar_hash] = job_key
    except Exception:
        _colorize_traceback()
        sys.exit(1)

    job.run_time = [5]
    job.cores = [1]
    job.dataTransferIns = [1, 1]
    job.dataTransferOut = 1

    job.storage_ids = [StorageID.GDRIVE, StorageID.GDRIVE]
    job.cache_types = [CacheType.PRIVATE, CacheType.PUBLIC]
    job.storage_hours = [1, 1]
    job.data_prices_set_block_numbers = [0, 0]

    for folder_to_share in job.folders_to_share:
        tar_hash = foldername_tar_hash[folder_to_share]
        # required to send string as bytes == str_data.encode('utf-8')
        job.source_code_hashes.append(Ebb.w3.toBytes(text=tar_hash))

    tar_hash = foldername_tar_hash[job.folders_to_share[0]]
    job_key = job_keys[tar_hash]
    log(f"==> job_key={job_key}")
    requester = Ebb.w3.toChecksumAddress(Ebb.w3.eth.accounts[account_id])
    try:
        job_price, _cost = cost(provider, requester, job, Ebb.eBlocBroker, Ebb.w3)
        log("==> Submitting the job")
        return job, Ebb.submit_job(provider, job_key, account_id, job_price, job)
    except Exception as e:
        raise e


if __name__ == "__main__":
    account_id = 1
    _from = Ebb.w3.toChecksumAddress(Ebb.w3.eth.accounts[account_id])

    # provider = "0x57b60037b82154ec7149142c606ba024fbb0f991"  # netlab
    provider = "0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49"  # home_vm-1
    try:
        job, tx_hash = gdrive_submit_job(provider, _from)
        log("")
        pprint(tar_hashes)
        log(f"==> source_code_hashes={job.source_code_hashes}")
        receipt = get_tx_status(tx_hash)
        if receipt["status"] == 1:
            logs = Ebb.eBlocBroker.events.LogJob().processReceipt(receipt, errors=DISCARD)
            pprint(vars(logs[0].args))
            try:
                log(f"==> job's index={logs[0].args['index']}")
                log("SUCCESS")
            except IndexError:
                logging.info("Transaction is reverted.")
    except Exception as e:
        if type(e).__name__ != "QuietExit":
            _colorize_traceback()
        sys.exit(1)

"""
    else:
        logging.info(f"job_key_flag={job_key_flag}")
        dir_path = os.path.dirname(folder_to_share)
        tar_hash, tar_path = compress_folder(folder_to_share)
        output = gdrive._list(tar_hash)
        if not output:
            key = gdrive._upload(dir_path, tar_hash)
            logging.info(gdrive._list(tar_hash))
        else:
            log(f"==> Requested file {tar_hash}.tar.gz is already uploaded", color="blue")
            logging.info(output)
            key = output.partition("\n")[0].split()[0]
            silent_remove(f"{dir_path}/{tar_hash}.tar.gz")  # created .tar.gz files are removed
            is_already_uploaded = True
"""
