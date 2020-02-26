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
from lib import (PROVIDER_ID, WHERE, CacheType, convert_byte_to_mb, log, silent_remove)
from lib_mongodb import add_item_shareid, find_key
from storage_class import Storage

mc = MongoClient()


class EudatClass(Storage):
    def __init__(self, loggedJob, jobInfo, requesterID, is_already_cached, oc):
        super(self.__class__, self).__init__(loggedJob, jobInfo, requesterID, is_already_cached, oc)
        self.shareID = {}
        self.tar_downloaded_path = {}
        self.source_code_hashes_to_process: List[str] = []
        for source_code_hash in self.source_code_hashes:
            self.source_code_hashes_to_process.append(config.w3.toText(source_code_hash))

    def cache_wrapper(self):
        for idx, folder_name in enumerate(self.source_code_hashes_to_process):
            status = self.cache(folder_name, idx)
            if not status:
                return False
        return True

    def cache(self, folder_name, _id) -> bool:
        status = self.is_cached(folder_name, _id)

        if self.cache_type[_id] == CacheType.PRIVATE.value:
            # Download into private directory at $HOME/.eBlocBroker/cache
            cached_folder = self.private_dir
        elif self.cache_type[_id] == CacheType.PUBLIC.value:
            cached_folder = self.public_dir

        cached_folder = f"{cached_folder}"
        cached_tar_file = f"{cached_folder}/{folder_name}.tar.gz"

        if status:
            self.folder_type_dict[folder_name] = "tar.gz"
            self.tar_downloaded_path[folder_name] = cached_tar_file
            return True

        if not os.path.isfile(cached_tar_file):
            # if os.path.isfile(cached_foldernnn + '/run.sh'):
            if os.path.isdir(cached_folder):
                res = (
                    subprocess.check_output(
                        ["bash", f"{lib.EBLOCPATH}/scripts/generateMD5sum.sh", f"{cached_folder}/{folder_name}.tar.gz"]
                    )
                    .decode("utf-8")
                    .strip()
                )
                if res == folder_name:  # Checking is already downloaded folder's hash matches with the given hash
                    self.folder_type_dict[folder_name] = "folder"
                    log(f"=> {folder_name} is already cached under the public directory.", "blue")
                    return True
                else:
                    self.folder_type_dict[folder_name] = "tar.gz"
                    if not self.eudat_download_folder(cached_folder, cached_folder, folder_name):
                        return False
            else:
                self.folder_type_dict[folder_name] = "tar.gz"
                if not self.eudat_download_folder(cached_folder, cached_folder, folder_name):
                    return False

            if (
                _id == 0
                and self.folder_type_dict[folder_name] == "tar.gz"
                and not self.is_run_exists_in_tar(cached_tar_file)
            ):
                silent_remove(cached_tar_file)
                return False
        else:
            # Here we already know that its tar.gz file
            self.folder_type_dict[folder_name] = "tar.gz"
            res = (
                subprocess.check_output(["bash", f"{lib.EBLOCPATH}/scripts/generateMD5sum.sh", cached_tar_file])
                .decode("utf-8")
                .strip()
            )
            if res == folder_name:
                # Checking is already downloaded folder's hash matches with the given hash
                log(f"=> {cached_tar_file} is already cached.", "blue")
                self.tar_downloaded_path[folder_name] = cached_tar_file
                self.folder_type_dict[folder_name] = "tar.gz"
                return True
            else:
                if not self.eudat_download_folder(cached_folder, cached_folder, folder_name):
                    return False
        return True

    def eudat_download_folder(self, results_folder_prev, results_folder, folder_name) -> bool:
        # Assumes job is sent as .tar.gz file
        cached_tar_file = f"{results_folder_prev}/{folder_name}.tar.gz"
        logging.info(f"[ {WHERE(1)} ] - Downloading output.zip for {folder_name} -> {cached_tar_file}")
        for attempt in range(5):
            try:
                f_name = f"/{folder_name}/{folder_name}.tar.gz"
                status = self.oc.get_file(f_name, cached_tar_file)
                self.tar_downloaded_path[folder_name] = cached_tar_file
                if status:
                    logging.info("Done")
                else:
                    logging.error("Something is wrong")
                    return False
            except Exception:
                logging.error(f"E: Failed to download eudat file.\n{traceback.format_exc()}")
                time.sleep(5)
            else:
                break
        else:
            status, result = refund(
                PROVIDER_ID, PROVIDER_ID, self.job_key, self.index, self.jobID, self.source_code_hashes
            )  # Complete refund backte requester
            if not status:
                logging.error(result)
            else:
                logging.info(f"refund()_tx_hash={result}")
            return False  # Should return back to Driver

        # TODO: check hash of the downloaded file is correct or not
        return True

    def eudat_get_share_token(self, fID):
        """Checks already shared or not."""
        folder_token_flag = {}
        if not os.path.isdir(self.private_dir):
            logging.error(f"{self.private_dir} does not exist")
            return False

        shareID_file = f"{self.private_dir}/{self.job_key}_shareID.json"
        accept_flag = 0
        for idx, source_code_hash_text in enumerate(self.source_code_hashes_to_process):
            folder_name = source_code_hash_text

            self.folder_type_dict[folder_name] = None  # Initialization
            if os.path.isdir(f"{lib.OWN_CLOUD_PATH}/{folder_name}"):
                logging.info(
                    f"Eudat shared folder({folder_name}) is already accepted and exists on the Eudat mounted folder."
                )
                if os.path.isfile(f"{lib.OWN_CLOUD_PATH}/{folder_name}/{folder_name}.tar.gz"):
                    self.folder_type_dict[folder_name] = "tar.gz"
                else:
                    self.folder_type_dict[folder_name] = "folder"
            try:
                info = self.oc.file_info(f"/{folder_name}/{folder_name}.tar.gz")
                size = info.attributes["{DAV:}getcontentlength"]
                folder_token_flag[folder_name] = True
                logging.info(f"index={idx} size of /{folder_name}/{folder_name}.tar.gz => {size} bytes")
                accept_flag += 1
            except Exception:
                folder_token_flag[folder_name] = False

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

            if status or (folder_token_flag[folder_name] and bool(self.shareID)):
                accept_flag += 1
            else:
                # eudatFolderName = ""
                logging.info("Searching share tokens for the related source code folder.")
                for idx in range(len(share_list) - 1, -1, -1):  # Starts iterating from last item to the first one
                    input_folder_name = share_list[idx]["name"]
                    input_folder_name = input_folder_name[1:]  # Removes '/' on the beginning of the string
                    _shareID = share_list[idx]["id"]
                    # inputOwner = share_list[i]['owner']
                    inputUser = f"{share_list[idx]['user']}@b2drop.eudat.eu"
                    if input_folder_name == folder_name and inputUser == fID:
                        self.share_token = str(share_list[idx]["share_token"])
                        self.shareID[folder_name] = {"shareID": int(_shareID), "share_token": self.share_token}
                        # Adding into mongodb for future usage
                        status = add_item_shareid(folder_name, _shareID, self.share_token)
                        if status:
                            logging.info("Successfull added into mongodb")
                        else:
                            logging.error("E: Something is wrong, Not added into mongodb")
                        # eudatFolderName = str(input_folder_name)
                        logging.info(f"Found. Name={folder_name} | ShareID={_shareID} | share_token={self.share_token}")
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
            if not self.is_already_cached[folder_name]:
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
                PROVIDER_ID, PROVIDER_ID, self.job_key, self.index, self.jobID, self.source_code_hashes
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

        for source_code_hash_text in self.source_code_hashes_to_process:
            folder_name = source_code_hash_text
            if self.folder_type_dict[folder_name] == "tar.gz":
                # Untar cached tar file into private directory
                tar_to_extract = self.tar_downloaded_path[folder_name]
                status, result = lib.execute_shell_command(
                    ["tar", "-xf", tar_to_extract, "--strip-components=1", "-C", self.results_folder]
                )
                if result != "":
                    print(result)

        if not os.path.isfile(f"{self.results_folder}/run.sh"):
            logging.error(f"{self.results_folder}/run.sh does not exist")
            return False

        logging.info(f"dataTransferIn={self.dataTransferIn}")
        try:
            self.share_token = self.shareID[self.job_key]["share_token"]
        except KeyError:
            status, self.share_token = find_key(mc["eBlocBroker"]["shareID"], self.job_key)
            if not status:
                logging.error(f"E: shareID cannot detected from key: {self.job_key}")
            return False

        if not self.sbatch_call():
            return False

        return True
