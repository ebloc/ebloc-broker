#!/usr/bin/env python3

import json
import os
import subprocess
import time
import traceback
from pdb import set_trace as bp
from typing import List

from pymongo import MongoClient

import config
import lib
from config import logging
from contractCalls.get_provider_info import get_provider_info
from contractCalls.refund import refund
from lib import (PROGRAM_PATH, PROVIDER_ID, CacheType, convert_byte_to_mb, log, sbatchCall,
                 silent_remove)
from lib_mongodb import add_item_shareid, find_key

mc = MongoClient()


class EudatClass:
    def __init__(self, loggedJob, jobInfo, requesterID, already_cached, oc):
        self.requesterID = requesterID
        self.jobInfo = jobInfo
        self.loggedJob = loggedJob
        self.jobKey = self.loggedJob.args["jobKey"]
        self.index = self.loggedJob.args["index"]
        self.jobID = 0
        self.private_dir = f"{PROGRAM_PATH}/{requesterID}/cache"
        self.public_dir = f"{PROGRAM_PATH}/cache"
        self.cache_type = loggedJob.args["cacheType"]
        self.source_code_hashes = loggedJob.args["sourceCodeHash"]
        self.dataTransferIn = jobInfo[0]["dataTransferIn"]
        self.already_cached = already_cached
        self.oc = oc
        self.shareID = {}
        self.folder_type_dict = {}
        self.tar_downloaded_path = {}
        self.glob_cache_folder = ""
        self.source_code_hashes_to_process: List[str] = []
        self.results_folder_prev = f"{PROGRAM_PATH}/{self.requesterID}/{self.jobKey}_{self.index}"
        self.results_folder = f"{self.results_folder_prev}/JOB_TO_RUN"

    def is_run_exist_in_tar(self, tarPath):
        try:
            FNULL = open(os.devnull, "w")
            res = (
                subprocess.check_output(["tar", "ztf", tarPath, "--wildcards", "*/run.sh"], stderr=FNULL)
                .decode("utf-8")
                .strip()
            )
            FNULL.close()
            if res.count("/") == 1:  # Main folder should contain the 'run.sh' file
                logging.info("./run.sh exists under the parent folder")
                return True
            else:
                logging.error("E: run.sh does not exist under the parent folder")
                return False
        except:
            logging.error("E: run.sh does not exist under the parent folder")
            return False

    def cache_wrapper(self):
        for idx, folder_name in enumerate(self.source_code_hashes_to_process):
            status = self.cache(folder_name, idx)
            if not status:
                return False
        return True

    def cache(self, folder_name, _id):
        if self.cache_type[_id] == CacheType.PRIVATE.value:
            # First checking does is already exist under public cache directory
            self.glob_cache_folder = self.public_dir
            if not os.path.isdir(self.glob_cache_folder):  # If folder does not exist
                os.makedirs(self.glob_cache_folder)

            cached_folder = f"{self.glob_cache_folder}/{folder_name}"
            cached_tar_file = f"{self.glob_cache_folder}/{folder_name}.tar.gz"
            if not os.path.isfile(cached_tar_file):
                if os.path.isfile(f"{cached_folder}/run.sh"):
                    res = (
                        subprocess.check_output(["bash", f"{lib.EBLOCPATH}/scripts/generateMD5sum.sh", cached_folder])
                        .decode("utf-8")
                        .strip()
                    )
                    if res == folder_name:  # Checking is already downloaded folder's hash matches with the given hash
                        self.folder_type_dict[folder_name] = "folder"
                        self.cache_type[_id] = CacheType.PUBLIC.value
                        logging.info("Already cached under the public directory...")
                        return True
            else:
                self.folder_type_dict[folder_name] = "tar.gz"
                res = (
                    subprocess.check_output(["bash", f"{lib.EBLOCPATH}/scripts/generateMD5sum.sh", cached_tar_file])
                    .decode("utf-8")
                    .strip()
                )
                if res == folder_name:  # Checking is already downloaded folder's hash matches with the given hash
                    self.cache_type[_id] = CacheType.PUBLIC.value
                    logging.info("Already cached under the public directory.")
                    return True

        if self.cache_type[_id] == CacheType.PRIVATE.value or self.cache_type[_id] == CacheType.PUBLIC.value:
            if self.cache_type[_id] == CacheType.PRIVATE.value:
                # Download into private directory at $HOME/.eBlocBroker/cache
                self.glob_cache_folder = self.private_dir
            elif self.cache_type[_id] == CacheType.PUBLIC.value:
                self.glob_cache_folder = self.public_dir

            if not os.path.isdir(self.glob_cache_folder):  # If folder does not exist
                os.makedirs(self.glob_cache_folder)

            cached_folder = f"{self.glob_cache_folder}/{folder_name}"
            cached_tar_file = f"{cached_folder}.tar.gz"

            if not os.path.isfile(cached_tar_file):
                # if os.path.isfile(cached_foldernnn + '/run.sh'):
                if os.path.isdir(cached_folder):
                    res = (
                        subprocess.check_output(
                            [
                                "bash",
                                f"{lib.EBLOCPATH}/scripts/generateMD5sum.sh",
                                f"{cached_folder}/{folder_name}.tar.gz",
                            ]
                        )
                        .decode("utf-8")
                        .strip()
                    )
                    if res == folder_name:  # Checking is already downloaded folder's hash matches with the given hash
                        self.folder_type_dict[folder_name] = "folder"
                        logging.info(f"{folder_name} is already cached under the public directory.")
                        return True
                    else:
                        if not self.eudat_download_folder(self.glob_cache_folder, cached_folder, folder_name):
                            return False
                else:
                    if not self.eudat_download_folder(self.glob_cache_folder, cached_folder, folder_name):
                        return False
                    self.folder_type_dict[folder_name] = "tar.gz"

                if (
                    _id == 0
                    and self.folder_type_dict[folder_name] == "tar.gz"
                    and not self.is_run_exist_in_tar(cached_tar_file)
                ):
                    silent_remove(cached_tar_file)
                    return False
            else:  # Here we already know that its tar.gz file
                self.folder_type_dict[folder_name] = "tar.gz"
                res = (
                    subprocess.check_output(["bash", f"{lib.EBLOCPATH}/scripts/generateMD5sum.sh", cached_tar_file])
                    .decode("utf-8")
                    .strip()
                )
                # if folder_type_dict[folder_name] == 'tar.gz':
                #    res = subprocess.check_output(['bash', lib.EBLOCPATH + '/scripts/generateMD5sum.sh', cached_tar_file]).decode('utf-8').strip()
                # elif folder_type_dict[folder_name] == 'folder':
                #    res = subprocess.check_output(['bash', lib.EBLOCPATH + '/scripts/generateMD5sum.sh', cached_folder]).decode('utf-8').strip()
                if res == folder_name:  # Checking is already downloaded folder's hash matches with the given hash
                    logging.info(f"{cached_tar_file} is already cached.")
                    self.tar_downloaded_path[folder_name] = cached_tar_file
                    return True
                else:
                    if not self.eudat_download_folder(self.glob_cache_folder, cached_folder, folder_name):
                        return False
        return True

    def eudat_download_folder(self, results_folder_prev, results_folder, folder_name) -> bool:
        # Assumes job is sent as .tar.gz file
        logging.info(f"Downloading output.zip for {folder_name} -> {results_folder_prev}/{folder_name}.tar.gz ...")
        for attempt in range(5):
            try:
                f_name = f"/{folder_name}/{folder_name}.tar.gz"
                cached_tar_file = f"{results_folder_prev}/{folder_name}.tar.gz"
                status = self.oc.get_file(f_name, cached_tar_file)
                self.tar_downloaded_path[folder_name] = cached_tar_file
                if status:
                    logging.info("Done")
                else:
                    return False
            except Exception:
                logging.error(f"E: Failed to download eudat file.\n{traceback.format_exc()}")
                time.sleep(5)
            else:
                break
        else:
            status, result = refund(
                PROVIDER_ID, PROVIDER_ID, self.jobKey, self.index, self.jobID, self.source_code_hashes
            )  # Complete refund backte requester
            if not status:
                logging.error(result)
            else:
                logging.info(f"refund()_tx_hash={result}")
            return False  # Should return back to Driver

        return True

    def eudat_get_share_token(self, fID):
        """Checks already shared or not."""
        folderTokenFlag = {}
        if not os.path.isdir(self.private_dir):
            logging.error(f"{self.private_dir} does not exist")
            return False

        shareID_file = f"{self.private_dir}/{self.jobKey}_shareID.json"
        accept_flag = 0
        for idx, source_code_hash_text in enumerate(self.source_code_hashes_to_process):
            folder_name = source_code_hash_text

            self.folder_type_dict[folder_name] = None  # Initialization
            if os.path.isdir(f"{lib.OWN_CLOUD_PATH}/{folder_name}"):
                logging.info(
                    f"Eudat shared folder({folder_name}) is already accepted and exists on the Eudat mounted folder..."
                )
                if os.path.isfile(f"{lib.OWN_CLOUD_PATH}/{folder_name}/{folder_name}.tar.gz"):
                    self.folder_type_dict[folder_name] = "tar.gz"
                else:
                    self.folder_type_dict[folder_name] = "folder"
            try:
                info = self.oc.file_info(f"/{folder_name}/{folder_name}.tar.gz")
                size = info.attributes["{DAV:}getcontentlength"]
                folderTokenFlag[folder_name] = True
                logging.info(f"index={idx} size of /{folder_name}/{folder_name}.tar.gz => {size} bytes")
                accept_flag += 1
            except Exception:
                folderTokenFlag[folder_name] = False

        if os.path.isfile(shareID_file) and os.path.getsize(shareID_file) > 0:
            with open(shareID_file) as json_file:
                self.shareID = json.load(json_file)

        logging.info(f"shareID_dict={self.shareID}")
        for attempt in range(5):
            try:
                share_list = self.oc.list_open_remote_share()
            except Exception:
                logging.error(f"E: Failed to list_open_remote_share eudat.\n{traceback.format_exc()}")
                time.sleep(1)
            else:
                break
        else:
            return False

        mongodb_accept_flag = 0
        accept_flag = 0
        for source_code_hash_text in self.source_code_hashes_to_process:
            folder_name = source_code_hash_text
            status, result = find_key(mc["eBlocBroker"]["shareID"], folder_name)
            if status:
                self.shareID[folder_name] = {"shareID": result["shareID"], "share_token": result["share_token"]}
                mongodb_accept_flag += 1

            if status or (folderTokenFlag[folder_name] and bool(self.shareID)):
                accept_flag += 1
            else:
                # eudatFolderName = ""
                logging.info("Searching share tokens for the related source code folder...")
                for idx in range(len(share_list) - 1, -1, -1):  # Starts iterating from last item to the first one
                    input_folder_name = share_list[idx]["name"]
                    input_folder_name = input_folder_name[1:]  # Removes '/' on the beginning of the string
                    _shareID = share_list[idx]["id"]
                    # inputOwner = share_list[i]['owner']
                    inputUser = f"{share_list[idx]['user']}@b2drop.eudat.eu"
                    if input_folder_name == folder_name and inputUser == fID:
                        share_token = str(share_list[idx]["share_token"])
                        self.shareID[folder_name] = {"shareID": int(_shareID), "share_token": share_token}
                        # Adding into mongodb for future usage
                        status = add_item_shareid(folder_name, _shareID, share_token)
                        if status:
                            logging.info("Successfull added into mongodb")
                        else:
                            logging.error("E: Something is wrong, Not added into mongodb")
                        # eudatFolderName = str(input_folder_name)
                        logging.info(f"Found. Name={folder_name} | ShareID={_shareID} | share_token={share_token}")
                        self.oc.accept_remote_share(int(_shareID))
                        logging.info("shareID is accepted.")
                        accept_flag += 1
                        break
            if accept_flag is len(self.source_code_hashes):
                break
        else:
            if mongodb_accept_flag is len(self.source_code_hashes):
                logging.info("Already exists on mongodb")
            else:
                logging.error(f"E: Couldn't find a shared file. Found ones are: {self.shareID}")
                return False

        if bool(self.shareID):
            with open(shareID_file, "w") as f:
                json.dump(self.shareID, f)
        else:
            logging.error("Something is wrong shareID is {}.")
            return False

        size_to_download = 0
        for source_code_hash_text in self.source_code_hashes_to_process:
            folder_name = source_code_hash_text
            if not self.already_cached[folder_name]:
                info = self.oc.file_info(f"/{folder_name}/{folder_name}.tar.gz")
                size_to_download += int(info.attributes["{DAV:}getcontentlength"])

        logging.info(f"Total size to download={size_to_download}")
        return True, int(convert_byte_to_mb(size_to_download))

    def run(self) -> bool:
        """
        # ----------
        # TODO: delete // refund check
        status, result = refund(PROVIDER_ID, PROVIDER_ID, jobKey, index, jobID, source_code_hashes)
        if not status:
            logging.error(result)
            return False
        else:
            logging.info(f"refund()_tx_hash={result}")
            return True
        sys.exit()
        # ----------
        """
        log(f"New job has been received. EUDAT call | {time.ctime()}", "blue")

        for source_code_hash in self.source_code_hashes:
            self.source_code_hashes_to_process.append(config.w3.toText(source_code_hash))

        status, provider_info = get_provider_info(self.loggedJob.args["provider"])
        status, used_dataTransferIn = self.eudat_get_share_token(provider_info["fID"])
        if not status:
            return False

        if used_dataTransferIn > self.dataTransferIn:
            # Full refund
            logging.error(
                "E: requested size to download the source code and data files is greater that the given amount."
            )
            status, result = refund(
                PROVIDER_ID, PROVIDER_ID, self.jobKey, self.index, self.jobID, self.source_code_hashes
            )
            if not status:
                logging.error(result)
                return False
            else:
                logging.info(f"refund()_tx_hash={result}")
                return True

        status = self.cache_wrapper()
        if not status:
            return False

        if not os.path.isdir(self.results_folder):
            os.makedirs(self.results_folder)

        for source_code_hash_text in self.source_code_hashes_to_process:
            folder_name = source_code_hash_text
            if self.folder_type_dict[folder_name] == "tar.gz":
                # Untar cached tar file into private directory
                tar_to_extract = self.tar_downloaded_path[folder_name]  # f"{self.glob_cache_folder}/{folder_name}.tar.gz"
                status, result = lib.execute_shell_command(
                    [
                        "tar",
                        "-xf",
                        tar_to_extract,
                        "--strip-components=1",
                        "-C",
                        self.results_folder,
                    ]
                )
                if result != "":
                    print(result)

        if not os.path.isfile(f"{self.results_folder}/run.sh"):
            logging.error(f"{self.results_folder}/run.sh does not exist")
            return False

        try:
            logging.info(f"dataTransferIn={self.dataTransferIn}")
            try:
                share_token = self.shareID[self.jobKey]["share_token"]
            except KeyError:
                status, share_token = find_key(mc["eBlocBroker"]["shareID"], self.jobKey)
                if not status:
                    logging.error(
                        f"E: Failed to call sbatchCall() function. shareID cannot detect key for {self.jobKey}"
                    )
                    return False

            sbatchCall(
                self.loggedJob,
                share_token,
                self.requesterID,
                self.results_folder,
                self.results_folder_prev,
                self.dataTransferIn,
                self.source_code_hashes,
                self.jobInfo,
            )
        except Exception:
            logging.error(f"E: Failed to call sbatchCall() function. {traceback.format_exc()}")
            return False

        return True
