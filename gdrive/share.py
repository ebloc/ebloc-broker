#!/usr/bin/env python3

import json
import os
import shutil
import subprocess
import sys
import traceback

from config import load_log
from contract.scripts.lib import cost
from contractCalls.get_provider_info import get_provider_info
from contractCalls.submitJob import submitJob
from imports import connect
from lib import (CacheType, StorageID, compress_folder, get_tx_status, printc,
                 silent_remove)
from lib_gdrive import gdrive_list, gdrive_upload_internal
from utils import read_json

log = load_log(f"output.log")

base_folder = "/home/netlab/eBlocBroker/gdrive/exampleFolderToShare/"


def create_meta_json(f_path, job_key_dict):
    with open(f_path, "w") as f:
        json.dump(job_key_dict, f)

    printc(f"meta_data.json file is updated on the base folder", "yellow")
    log.info(f"{job_key_dict}")


def gdrive_upload(folder_to_share, job_key_flag=False):
    already_uploaded = False
    if job_key_flag:
        log.info(f"job_key_flag={job_key_flag} | tar.gz file is inside a folder")
        dir_path = os.path.dirname(folder_to_share)
        tar_hash = compress_folder(folder_to_share)

        path_to_move = f"{dir_path}/{tar_hash}"
        if not os.path.exists(path_to_move):
            os.makedirs(path_to_move)

        shutil.move(f"{dir_path}/{tar_hash}.tar.gz", f"{path_to_move}/{tar_hash}.tar.gz")
        shutil.copyfile(f"{base_folder}/meta_data.json", f"{path_to_move}/meta_data.json")

        output = gdrive_list(tar_hash, True)
        if not output:
            key = gdrive_upload_internal(dir_path, tar_hash, True)
            print(gdrive_list(tar_hash))
        else:
            printc(f"=> Requested folder {tar_hash} is already uploaded", "blue")
            log.info(output)
            key = output.partition("\n")[0].split()[0]
            already_uploaded = True

        silent_remove(f"{dir_path}/{tar_hash}")  # created .tar.gz files are removed

    else:
        log.info(f"job_key_flag={job_key_flag}")
        dir_path = os.path.dirname(folder_to_share)
        tar_hash = compress_folder(folder_to_share)
        output = gdrive_list(tar_hash)
        if not output:
            key = gdrive_upload_internal(dir_path, tar_hash)
            print(gdrive_list(tar_hash))
        else:
            printc(f"=> Requested file {tar_hash}.tar.gz is already uploaded", "blue")
            print(output)
            key = output.partition("\n")[0].split()[0]
            silent_remove(f"{dir_path}/{tar_hash}.tar.gz")  # created .tar.gz files are removed
            already_uploaded = True

    return key, already_uploaded, tar_hash


def share_folder(folder_to_share, provider_to_share, job_key_flag=False):
    log.info(f"folder_to_share={folder_to_share}")
    job_key, already_uploaded, tar_hash = gdrive_upload(folder_to_share, job_key_flag)
    log.info(f"job_key={job_key}")
    # cmd: gdrive share $job_key --role writer --type user --email $provider_to_share
    if not already_uploaded:
        output = (
            subprocess.check_output(
                ["gdrive", "share", job_key, "--role", "writer", "--type", "user", "--email", provider_to_share,]
            )
            .decode("utf-8")
            .strip()
        )
        log.info(f"share_output={output}")

    return job_key, tar_hash


def gdrive_submit_job(provider):
    eBlocBroker, w3 = connect()
    if eBlocBroker is None or w3 is None:
        return False, "web3 is not connected"

    account_id = 1
    provider = w3.toChecksumAddress(provider)  # netlab
    provider_to_share = "alper.alimoglu@gmail.com"  # 'alper01234alper@gmail.com'
    success, provider_info = get_provider_info(provider)
    folder_to_share_list = []  # Path of folder to share

    # Full path of the sourceCodeFolders is given
    job_key_dict = {}
    source_code_hash_list = []
    folderName_tar_hash = {}

    sourceCodePath = f"{base_folder}/sourceCode"
    folder_to_share_list.append(sourceCodePath)  # sourceCode at index 0
    folder_to_share_list.append(f"{base_folder}/data1")
    # subprocess.run(['sudo', 'chmod', '-R', '777', folder_to_share])

    try:
        if len(folder_to_share_list) > 1:
            for folder_to_share in folder_to_share_list[1:]:
                # Starting from the first element ignoring source_folder
                # Attempting to share the data folder
                job_key, tar_hash = share_folder(folder_to_share, provider_to_share)
                folderName_tar_hash[folder_to_share] = tar_hash
                job_key_dict[tar_hash] = job_key

            data_files_json_path = f"{base_folder}/meta_data.json"
            success, data_json = read_json(data_files_json_path)
            if success:
                if job_key_dict == data_json:
                    printc("meta_data.json file already exists", "blue")
                else:
                    create_meta_json(f"{base_folder}/meta_data.json", job_key_dict)
            else:
                create_meta_json(f"{base_folder}/meta_data.json", job_key_dict)

        folder_to_share = folder_to_share_list[0]
        job_key, tar_hash = share_folder(folder_to_share, provider_to_share, True)
        folderName_tar_hash[folder_to_share] = tar_hash
        job_key_dict[tar_hash] = job_key
    except Exception:
        log.error(f"E: {traceback.format_exc()}")
        sys.exit(1)

    coreMin_list = []
    coreMin_list.append(5)
    core_list = [1]
    dataTransferIn_list = [1, 1]
    dataTransferOut = 1

    storageID_list = [StorageID.GDRIVE.value, StorageID.GDRIVE.value]
    cacheType_list = [
        CacheType.PRIVATE.value,
        CacheType.PUBLIC.value,
    ]  # Covers public and private folders
    storage_hour_list = [1, 1]
    data_prices_set_blocknumber_list = [0, 0]

    for folder_to_share in folder_to_share_list:
        tar_hash = folderName_tar_hash[folder_to_share]
        source_code_hash = w3.toBytes(text=tar_hash)  # Required to send string as bytes == str_data.encode('utf-8')
        source_code_hash_list.append(source_code_hash)

    tar_hash = folderName_tar_hash[folder_to_share_list[0]]
    jobKey = job_key_dict[tar_hash]
    log.info(f"job_key={jobKey}")

    requester = w3.toChecksumAddress(w3.eth.accounts[account_id])
    job_price_value, _cost = cost(
        core_list,
        coreMin_list,
        provider,
        requester,
        source_code_hash_list,
        dataTransferIn_list,
        dataTransferOut,
        storage_hour_list,
        storageID_list,
        cacheType_list,
        data_prices_set_blocknumber_list,
        eBlocBroker,
        w3,
        False,
    )

    log.info("\nSubmitting Job...")
    success, output = submitJob(
        provider,
        jobKey,
        core_list,
        coreMin_list,
        dataTransferIn_list,
        dataTransferOut,
        storageID_list,
        source_code_hash_list,
        cacheType_list,
        storage_hour_list,
        account_id,
        job_price_value,
        data_prices_set_blocknumber_list,
    )

    return success, output


if __name__ == "__main__":
    eBlocBroker, w3 = connect()
    provider = "0x57b60037b82154ec7149142c606ba024fbb0f991"  # netlab
    success, output = gdrive_submit_job(provider)

    if not success:
        log.info(output)
        sys.exit(1)
    else:
        receipt = get_tx_status(success, output)
        if receipt["status"] == 1:
            logs = eBlocBroker.events.LogJob().processReceipt(receipt)
            try:
                log.info(f"Job's index={logs[0].args['index']}")
            except IndexError:
                log.info("Transaction is reverted.")
