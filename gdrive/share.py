#!/usr/bin/env python3

import json
import os
import shutil
import sys
import traceback

from config import bp, logging, EBLOCPATH  # noqa: F401
from contract.scripts.lib import cost
from contractCalls.get_provider_info import get_provider_info
from contractCalls.submitJob import submitJob
from imports import connect
from lib import CacheType, StorageID, compress_folder, get_tx_status, printc, run_command, silent_remove
from lib_gdrive import gdrive_list, gdrive_upload_internal
from lib_git import git_commit_changes
from utils import read_json

base_folder = f"{EBLOCPATH}/base"


def create_meta_json(f_path, job_key_dict):
    with open(f_path, "w") as f:
        json.dump(job_key_dict, f)

    printc(f"meta_data.json file is updated on the base folder", "yellow")
    logging.info(f"{job_key_dict}")


def gdrive_upload(folder_to_share, job_key_flag=False):
    already_uploaded = False
    logging.info(f"job_key_flag={job_key_flag} | tar.gz file is inside a folder")
    dir_path = os.path.dirname(folder_to_share)
    tar_hash = compress_folder(folder_to_share)

    path_to_move = f"{dir_path}/{tar_hash}"
    if not os.path.exists(path_to_move):
        os.makedirs(path_to_move)

    shutil.move(f"{dir_path}/{tar_hash}.tar.gz", f"{path_to_move}/{tar_hash}.tar.gz")
    if job_key_flag:
        shutil.copyfile(f"{base_folder}/meta_data.json", f"{path_to_move}/meta_data.json")

    output = gdrive_list(tar_hash, True)
    if not output:
        key = gdrive_upload_internal(dir_path, tar_hash, True)
        logging.info(gdrive_list(tar_hash))
    else:
        printc(f"=> Requested folder {tar_hash} is already uploaded", "blue")
        logging.info(output)
        key = output.partition("\n")[0].split()[0]
        already_uploaded = True

    silent_remove(f"{dir_path}/{tar_hash}")  # created .tar.gz files are removed

    """
    else:
        logging.info(f"job_key_flag={job_key_flag}")
        dir_path = os.path.dirname(folder_to_share)
        tar_hash = compress_folder(folder_to_share)
        output = gdrive_list(tar_hash)
        if not output:
            key = gdrive_upload_internal(dir_path, tar_hash)
            logging.info(gdrive_list(tar_hash))
        else:
            printc(f"=> Requested file {tar_hash}.tar.gz is already uploaded", "blue")
            logging.info(output)
            key = output.partition("\n")[0].split()[0]
            silent_remove(f"{dir_path}/{tar_hash}.tar.gz")  # created .tar.gz files are removed
            already_uploaded = True
    """
    return key, already_uploaded, tar_hash


def share_folder(folder_to_share, provider_to_share, job_key_flag=False):
    logging.info(f"folder_to_share={folder_to_share}")
    job_key, already_uploaded, tar_hash = gdrive_upload(folder_to_share, job_key_flag)
    logging.info(f"job_key={job_key}")
    if not already_uploaded:
        cmd = ["gdrive", "share", job_key, "--role", "writer", "--type", "user", "--email", provider_to_share]
        success, output = run_command(cmd)
        logging.info(f"share_output={output}")

    return job_key, tar_hash


def gdrive_submit_job(provider):
    eBlocBroker, w3 = connect()
    if eBlocBroker is None or w3 is None:
        return False, "web3 is not connected"

    provider = w3.toChecksumAddress(provider)
    provider_to_share = "alper01234alper@gmail.com"  # "alper.alimoglu@gmail.com"  # '
    success, provider_info = get_provider_info(provider)
    account_id = 1

    folders_to_share = []
    # Full path of the sourceCodeFolders is given
    job_key_dict = {}
    source_code_hash_list = []
    folderName_tar_hash = {}

    # sourceCode at index 0
    folders_to_share.append(f"{base_folder}/sourceCode")
    folders_to_share.append(f"{base_folder}/data/data1")
    # subprocess.run(['sudo', 'chmod', '-R', '777', folder_to_share])

    for idx, folder in enumerate(folders_to_share):
        printc(folder, "green")
        success = git_commit_changes(folder)
        if not success:
            sys.exit(1)

    try:
        if len(folders_to_share) > 1:
            for folder_to_share in folders_to_share[1:]:
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

        folder_to_share = folders_to_share[0]
        job_key, tar_hash = share_folder(folder_to_share, provider_to_share, True)
        folderName_tar_hash[folder_to_share] = tar_hash
        job_key_dict[tar_hash] = job_key
    except Exception:
        logging.error(f"E: {traceback.format_exc()}")
        sys.exit(1)

    coreMin_list = []
    coreMin_list.append(5)
    core_list = [1]
    dataTransferIn_list = [1, 1]
    dataTransferOut = 1

    storage_ids = [StorageID.GDRIVE.value, StorageID.GDRIVE.value]
    cacheType_list = [CacheType.PRIVATE.value, CacheType.PUBLIC.value]  # Covers public and private folders
    storage_hours = [1, 1]
    data_prices_set_blocknumbers = [0, 0]

    for folder_to_share in folders_to_share:
        tar_hash = folderName_tar_hash[folder_to_share]
        # Required to send string as bytes == str_data.encode('utf-8')
        source_code_hash = w3.toBytes(text=tar_hash)
        source_code_hash_list.append(source_code_hash)

    tar_hash = folderName_tar_hash[folders_to_share[0]]
    jobKey = job_key_dict[tar_hash]
    logging.info(f"job_key={jobKey}")

    requester = w3.toChecksumAddress(w3.eth.accounts[account_id])
    job_price_value, _cost = cost(
        core_list,
        coreMin_list,
        provider,
        requester,
        source_code_hash_list,
        dataTransferIn_list,
        dataTransferOut,
        storage_hours,
        storage_ids,
        cacheType_list,
        data_prices_set_blocknumbers,
        eBlocBroker,
        w3,
        False,
    )

    logging.info("\nSubmitting Job...")
    success, output = submitJob(
        provider,
        jobKey,
        core_list,
        coreMin_list,
        dataTransferIn_list,
        dataTransferOut,
        storage_ids,
        source_code_hash_list,
        cacheType_list,
        storage_hours,
        account_id,
        job_price_value,
        data_prices_set_blocknumbers,
    )

    return success, output


if __name__ == "__main__":
    eBlocBroker, w3 = connect()
    # provider = "0x57b60037b82154ec7149142c606ba024fbb0f991"  # netlab
    provider = "0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49"  # home-vm
    success, output = gdrive_submit_job(provider)

    if not success:
        logging.error(output)
        sys.exit(1)
    else:
        receipt = get_tx_status(success, output)
        if receipt["status"] == 1:
            logs = eBlocBroker.events.LogJob().processReceipt(receipt)
            try:
                logging.info(f"Job's index={logs[0].args['index']}")
            except IndexError:
                logging.info("Transaction is reverted.")
