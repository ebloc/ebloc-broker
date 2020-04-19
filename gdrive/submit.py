#!/usr/bin/env python3

import json
import os
import shutil
import sys

import libs.gdrive as gdrive
import libs.git as git
from config import bp, env, logging  # noqa: F401
from contract.scripts.lib import Job, cost
from contractCalls.submitJob import submitJob
from imports import connect
from lib import CacheType, StorageID, compress_folder, get_tx_status, printc, run, silent_remove
from utils import _colorize_traceback, read_json

base_folder = f"{env.EBLOCPATH}/base"


def create_meta_json(filename, job_keys):
    with open(filename, "w") as f:
        json.dump(job_keys, f)

    printc(f"meta_data.json file is updated into the base folder", "yellow")
    logging.info(job_keys)


def gdrive_upload(folder_to_share, job_key_flag=False):
    is_already_uploaded = False
    logging.info(f"job_key_flag={job_key_flag} | tar.gz file is inside a folder")
    dir_path = os.path.dirname(folder_to_share)
    tar_hash, tar_path = compress_folder(folder_to_share)

    path_to_move = f"{dir_path}/{tar_hash}"
    if not os.path.exists(path_to_move):
        os.makedirs(path_to_move)

    shutil.move(f"{dir_path}/{tar_hash}.tar.gz", f"{path_to_move}/{tar_hash}.tar.gz")
    if job_key_flag:
        shutil.copyfile(f"{base_folder}/meta_data.json", f"{path_to_move}/meta_data.json")

    is_file_exist = gdrive.list(tar_hash, is_folder=True)
    if not is_file_exist:
        key = gdrive.upload_internal(dir_path, tar_hash, True)
        logging.info(gdrive.list(tar_hash))
    else:
        printc(f"=> Requested folder {tar_hash} is already uploaded", "blue")
        logging.info(is_file_exist)
        key = is_file_exist.partition("\n")[0].split()[0]
        is_already_uploaded = True

    silent_remove(f"{dir_path}/{tar_hash}")  # created .tar.gz files are removed
    return key, is_already_uploaded, tar_hash


def share_folder(folder_to_share, provider, job_key_flag=False):
    logging.info(f"folder_to_share={folder_to_share}")
    key, is_already_uploaded, tar_hash = gdrive_upload(folder_to_share, job_key_flag)
    logging.info(f"job_key={key}")
    cmd = ["gdrive", "share", key, "--role", "writer", "--type", "user", "--email", provider]
    if not is_already_uploaded:
        logging.info(f"share_output={run(cmd)}")

    return key, tar_hash


def gdrive_submit_job(provider):
    eBlocBroker, w3 = connect()
    job = Job()

    provider = w3.toChecksumAddress(provider)
    provider_to_share = "alper01234alper@gmail.com"  # "alper.alimoglu@gmail.com"  # '
    # provider_info = get_provider_info(provider)
    account_id = 1

    job_keys = {}
    foldername_tar_hash = {}

    job.folders_to_share.append(f"{base_folder}/sourceCode")
    job.folders_to_share.append(f"{base_folder}/data/data1")
    # subprocess.run(['sudo', 'chmod', '-R', '777', folder_to_share])

    for idx, folder in enumerate(job.folders_to_share):
        printc(folder, "green")
        try:
            git.initialize_check(folder)
            git.commit_changes(folder)
        except:
            sys.exit(1)

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
                    printc("meta_data.json file already exists", "blue")
                else:
                    create_meta_json(f"{base_folder}/meta_data.json", job_keys)
            except:
                create_meta_json(f"{base_folder}/meta_data.json", job_keys)

        folder_to_share = job.folders_to_share[0]
        job_key, tar_hash = share_folder(folder_to_share, provider_to_share, job_key_flag=True)
        foldername_tar_hash[folder_to_share] = tar_hash
        job_keys[tar_hash] = job_key
    except Exception:
        logging.error(_colorize_traceback())
        sys.exit(1)

    job.core_execution_durations = [5]
    job.cores = [1]
    job.dataTransferIns = [1, 1]
    job.dataTransferOut = 1

    job.storage_ids = [StorageID.GDRIVE.value, StorageID.GDRIVE.value]
    job.cache_types = [CacheType.PRIVATE.value, CacheType.PUBLIC.value]
    job.storage_hours = [1, 1]
    job.data_prices_set_block_numbers = [0, 0]

    for folder_to_share in job.folders_to_share:
        tar_hash = foldername_tar_hash[folder_to_share]
        # required to send string as bytes == str_data.encode('utf-8')
        job.source_code_hashes.append(w3.toBytes(text=tar_hash))

    tar_hash = foldername_tar_hash[job.folders_to_share[0]]
    job_key = job_keys[tar_hash]
    logging.info(f"job_key={job_key}")

    requester = w3.toChecksumAddress(w3.eth.accounts[account_id])
    job_price, _cost = cost(provider, requester, job, eBlocBroker, w3)
    logging.info("\nSubmitting the job")
    try:
        return submitJob(provider, job_key, account_id, job_price, job)
    except:
        logging.error(_colorize_traceback())
        raise


if __name__ == "__main__":
    eBlocBroker, w3 = connect()
    provider = "0x57b60037b82154ec7149142c606ba024fbb0f991"  # netlab
    # provider = "0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49"  # home-vm
    try:
        tx_hash = gdrive_submit_job(provider)
        receipt = get_tx_status(tx_hash)
        if receipt["status"] == 1:
            logs = eBlocBroker.events.LogJob().processReceipt(receipt)
            try:
                logging.info(f"Job's index={logs[0].args['index']}")
            except IndexError:
                logging.info("Transaction is reverted.")
    except:
        logging.error(_colorize_traceback())
        sys.exit(1)

"""
    else:
        logging.info(f"job_key_flag={job_key_flag}")
        dir_path = os.path.dirname(folder_to_share)
        tar_hash, tar_path = compress_folder(folder_to_share)
        output = gdrive.list(tar_hash)
        if not output:
            key = gdrive.upload_internal(dir_path, tar_hash)
            logging.info(gdrive.list(tar_hash))
        else:
            printc(f"=> Requested file {tar_hash}.tar.gz is already uploaded", "blue")
            logging.info(output)
            key = output.partition("\n")[0].split()[0]
            silent_remove(f"{dir_path}/{tar_hash}.tar.gz")  # created .tar.gz files are removed
            is_already_uploaded = True
"""
