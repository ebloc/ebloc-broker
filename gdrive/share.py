#!/usr/bin/env python3

import json
import os
import pprint
import shutil
import subprocess
import sys
import traceback

from contract.scripts.lib import cost
from contractCalls.get_provider_info import get_provider_info
from contractCalls.submitJob import submitJob
from imports import connect
from lib import CacheType, StorageID, compress_folder, printc
from lib_gdrive import gdrive_list, gdrive_upload_process


def gdrive_upload(folder_to_share, job_key_flag=False):
    already_uploaded = False
    if job_key_flag:  # tar.gz inside a folder
        dir_path = os.path.dirname(folder_to_share)
        tar_hash = compress_folder(folder_to_share)
        if not os.path.exists(dir_path + "/" + tar_hash):
            os.mkdir(dir_path + "/" + tar_hash)

        shutil.move(dir_path + "/" + tar_hash + ".tar.gz", dir_path + "/" + tar_hash + "/" + tar_hash + ".tar.gz")
        shutil.copyfile(folder_to_share + "/dataFiles.json", dir_path + "/" + tar_hash + "/dataFiles.json")

        res = gdrive_list(tar_hash, True)
        if res == "":
            key = gdrive_upload_process(dir_path, tar_hash, True)
        else:
            printc("Requested folder " + tar_hash + " is already uploaded", "green")
            print(res)
            key = res.partition("\n")[0].split()[0]
            already_uploaded = True

        shutil.rmtree(f"{dir_path}/{tar_hash}")  # created .tar.gz files are removed

    else:
        dir_path = os.path.dirname(folder_to_share)
        tar_hash = compress_folder(folder_to_share)
        res = gdrive_list(tar_hash)
        if res == "":
            key = gdrive_upload_process(dir_path, tar_hash)
        else:
            printc("Requested file " + tar_hash + ".tar.gz" + " is already uploaded", "green")
            key = res.partition("\n")[0].split()[0]
            subprocess.run(["rm", "-f", dir_path + "/" + tar_hash + ".tar.gz"])  # created .tar.gz files are removed
            already_uploaded = True

    return key, already_uploaded, tar_hash


def share_folder(folder_to_share, providerToShare, job_key_flag=False):
    print("folder_to_share=" + folder_to_share)
    job_key, already_uploaded, tar_hash = gdrive_upload(folder_to_share, job_key_flag)
    print(f"job_key={job_key}")
    # cmd: gdrive share $job_key --role writer --type user --email $providerToShare
    if not already_uploaded:
        res = (
            subprocess.check_output(
                ["gdrive", "share", job_key, "--role", "writer", "--type", "user", "--email", providerToShare]
            )
            .decode("utf-8")
            .strip()
        )
        print("share_output=" + res)

    return job_key, tar_hash


def gdrive_submit_job(provider):
    eBlocBroker, w3 = connect()
    if eBlocBroker is None or w3 is None:
        return False, "web3 is not connected"

    accountID = 0
    provider = w3.toChecksumAddress(provider)  # netlab
    providerToShare = "alper.alimoglu@gmail.com"  # 'alper01234alper@gmail.com'
    status, provider_info = get_provider_info(provider)
    folder_to_share_list = []  # Path of folder to share

    # Full path of the sourceCodeFolders is given
    jobKey_dict = {}
    source_code_hash_list = []
    folderName_tar_hash = {}

    sourceCodePath = "/home/netlab/eBlocBroker/gdrive/exampleFolderToShare/sourceCode"
    folder_to_share_list.append(sourceCodePath)  # sourceCode at index 0
    folder_to_share_list.append("/home/netlab/eBlocBroker/gdrive/exampleFolderToShare/data1")
    # subprocess.run(['sudo', 'chmod', '-R', '777', folder_to_share])

    try:
        if len(folder_to_share_list) > 1:
            for i in range(1, len(folder_to_share_list)):
                folder_to_share = folder_to_share_list[i]
                # Attempting to share the data folder
                job_key, tar_hash = share_folder(folder_to_share, providerToShare)
                folderName_tar_hash[folder_to_share] = tar_hash
                jobKey_dict[tar_hash] = job_key

            dataFileJson_path = folder_to_share_list[0] + "/dataFiles.json"
            if os.path.isfile(dataFileJson_path):
                with open(dataFileJson_path) as json_file:
                    data_json = json.load(json_file)

            if os.path.isfile(dataFileJson_path) and jobKey_dict == data_json:
                printc("dataFile.json file already exists", "green")
            else:
                with open(sourceCodePath + "/dataFiles.json", "w") as f:
                    json.dump(jobKey_dict, f)
                printc("dataFile.json file is updated on the sourceCode folder", "blue")

        folder_to_share = folder_to_share_list[0]
        job_key, tar_hash = share_folder(folder_to_share, providerToShare, True)
        folderName_tar_hash[folder_to_share] = tar_hash
        jobKey_dict[tar_hash] = job_key
    except Exception as e:
        print(f"E: {traceback.format_exc()}")
        sys.exit()

    coreMin_list = []
    coreMin_list.append(5)
    core_list = [1]
    dataTransferIn_list = [1, 1]
    dataTransferOut = 1

    storageID_list = [StorageID.GDRIVE.value, StorageID.GDRIVE.value]
    cacheType_list = [CacheType.PUBLIC.value, CacheType.PUBLIC.value]
    storageHour_list = [0, 0]
    data_prices_set_blocknumber_list = [0, 0]

    for i in range(0, len(folder_to_share_list)):
        _tar_hash = folderName_tar_hash[folder_to_share_list[i]]
        sourceCodeHash = w3.toBytes(text=_tar_hash)  # Required to send string as bytes == str_data.encode('utf-8')
        source_code_hash_list.append(sourceCodeHash)

    _tar_hash = folderName_tar_hash[folder_to_share_list[0]]
    jobKey = jobKey_dict[_tar_hash]
    print(f"job_key={jobKey}")

    requester = w3.toChecksumAddress(w3.eth.accounts[accountID])
    jobPriceValue, _cost = cost(
        core_list,
        coreMin_list,
        provider,
        requester,
        source_code_hash_list,
        dataTransferIn_list,
        dataTransferOut,
        storageHour_list,
        storageID_list,
        cacheType_list,
        data_prices_set_blocknumber_list,
        eBlocBroker,
        w3,
        False,
    )

    print("\nSubmitting Job...")
    status, result = submitJob(
        provider,
        jobKey,
        core_list,
        coreMin_list,
        dataTransferIn_list,
        dataTransferOut,
        storageID_list,
        source_code_hash_list,
        cacheType_list,
        storageHour_list,
        accountID,
        jobPriceValue,
        data_prices_set_blocknumber_list,
    )

    return status, result


if __name__ == "__main__":
    eBlocBroker, w3 = connect()
    provider = "0x57b60037b82154ec7149142c606ba024fbb0f991"  # netlab
    status, result = gdrive_submit_job(provider)

    if not status:
        print(result)
        sys.exit()
    else:
        print("tx_hash=" + result)
        receipt = w3.eth.waitForTransactionReceipt(result)
        print("Transaction receipt mined: \n")
        pprint.pprint(dict(receipt))
        print("Was transaction successful?")
        pprint.pprint(receipt["status"])
        if receipt["status"] == 1:
            logs = eBlocBroker.events.LogJob().processReceipt(receipt)
            try:
                print("Job's index=" + str(logs[0].args["index"]))
            except IndexError:
                print("Transaction is reverted.")


""" delete
    if folderType == 'folder':
        tar_hash = subprocess.check_output(['../scripts/generateMD5sum.sh', folder_to_share]).decode('utf-8').strip()
        tar_hash = tar_hash.split(' ', 1)[0]
        print('hash=' + tar_hash)

        if not os.path.isdir(tar_hash):
            subprocess.run(['cp', '-a', folder_to_share, tar_hash])

        folder_to_share = tar_hashn
        #cmd: gdrive list --query "name contains 'exampleFolderToShare'" --no-header
        res = subprocess.check_output(['gdrive', 'list', '--query', 'name contains \'' + folder_to_share + '\'', '--no-header']).decode('utf-8').strip()
        if res is '':
            print('Uploading ...')
            #cmd: gdrive upload --recursive $folder_to_share
            res = subprocess.check_output(['gdrive', 'upload', '--recursive', folder_to_share]).decode('utf-8').strip()
            print(res)
            res = subprocess.check_output(['gdrive', 'list', '--query', 'name contains \'' + folder_to_share + '\'', '--no-header']).decode('utf-8').strip()
            key = res.split(' ')[0]
    elif folderType == 'zip':
        # zip -r myfiles.zip mydir
        subprocess.run(['zip', '-r', folder_to_share + '.zip', folder_to_share])
        tar_hash = subprocess.check_output(['md5sum', folder_to_share + '.zip']).decode('utf-8').strip()
        tar_hash = tar_hash.split(' ', 1)[0]

        shutil.move(folder_to_share + '.zip', tar_hash + '.zip')

        subprocess.run(['mv', folder_to_share + '.zip', tar_hash + '.zip'])

        subprocess.run(['gdrive', 'upload', tar_hash + '.zip'])
        subprocess.run(['rm', '-f', tar_hash + '.zip'])
        print('hash=' + tar_hash)
        res = subprocess.check_output(['gdrive', 'list', '--query', 'name contains \'' + tar_hash + '.zip' + '\'', '--no-header']).decode('utf-8').strip()
        key = res.split(' ')[0]
"""
