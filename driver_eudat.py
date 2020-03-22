#!/usr/bin/env python3

import json
import os
import time
import traceback
from typing import List

from pymongo import MongoClient

import config
import lib
from config import logging
from contractCalls.get_provider_info import get_provider_info
from lib import WHERE, CacheType, log, silent_remove
from lib_mongodb import add_item_share_id, find_key
from storage_class import Storage
from utils import Link, byte_to_mb, create_dir, generate_md5sum, read_json

mc = MongoClient()


class EudatClass(Storage):
    def __init__(self, logged_job, jobInfo, requesterID, is_already_cached, oc):
        super(self.__class__, self).__init__(logged_job, jobInfo, requesterID, is_already_cached, oc)
        self.shareID = {}
        self.tar_downloaded_path = {}
        self.source_code_hashes_to_process: List[str] = []
        for source_code_hash in self.source_code_hashes:
            self.source_code_hashes_to_process.append(config.w3.toText(source_code_hash))

    def cache_wrapper(self) -> bool:
        for idx, folder_name in enumerate(self.source_code_hashes_to_process):
            success = self.cache(folder_name, idx)
            if not success:
                return False
        return True

    def cache(self, folder_name, id) -> bool:
        success = self.is_cached(folder_name, id)
        cached_folder = ""
        if self.cache_type[id] == CacheType.PRIVATE.value:
            # Download into private directory at $HOME/.eBlocBroker/cache
            cached_folder = self.private_dir
        elif self.cache_type[id] == CacheType.PUBLIC.value:
            cached_folder = self.public_dir

        cached_tar_file = f"{cached_folder}/{folder_name}.tar.gz"

        if success:
            self.folder_type_dict[folder_name] = "tar.gz"
            self.tar_downloaded_path[folder_name] = cached_tar_file
            return True

        if not os.path.isfile(cached_tar_file):
            # if os.path.isfile(cached_foldernnn + '/run.sh'):
            if os.path.isdir(cached_folder):
                output = generate_md5sum(f"{cached_folder}/{folder_name}.tar.gz")
                if output == folder_name:
                    # Checking is already downloaded folder's hash matches with the given hash
                    self.folder_type_dict[folder_name] = "folder"
                    log(
                        f"=> {folder_name} is already cached under the public directory.", "blue",
                    )
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
                id == 0
                and self.folder_type_dict[folder_name] == "tar.gz"
                and not self.is_run_exists_in_tar(cached_tar_file)
            ):
                silent_remove(cached_tar_file)
                return False
        else:
            # Here we already know that its tar.gz file
            self.folder_type_dict[folder_name] = "tar.gz"
            output = generate_md5sum(cached_tar_file)
            if output == folder_name:
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
                f = f"/{folder_name}/{folder_name}.tar.gz"
                success = self.oc.get_file(f, cached_tar_file)
                self.tar_downloaded_path[folder_name] = cached_tar_file
                if success:
                    logging.info("Done")
                else:
                    logging.error("Something is wrong")
                    return False
            except Exception:
                logging.error(f"E: Failed to download eudat file.\n{traceback.format_exc()}")
                logging.warning("Waiting for 5 seconds...")
                time.sleep(5)
            else:
                break
        else:
            success = self.complete_refund()
            return False  # Should return back to Driver

        # TODO: check hash of the downloaded file is correct or not
        return True

    def eudat_get_share_token(self, f_id):
        """Checks already shared or not."""
        folder_token_flag = {}
        if not os.path.isdir(self.private_dir):
            logging.error(f"{self.private_dir} does not exist")
            return False

        shareID_file = f"{self.private_dir}/{self.job_key}_shareID.json"
        accept_flag = 0
        for idx, source_code_hash_text in enumerate(self.source_code_hashes_to_process):
            folder_name = source_code_hash_text
            self.folder_type_dict[folder_name] = None
            if os.path.isdir(f"{lib.OWN_CLOUD_PATH}/{folder_name}"):
                logging.info(
                    f"Eudat shared folder({folder_name}) is already accepted and exists on the eudat mounted folder."
                )
                if os.path.isfile(f"{lib.OWN_CLOUD_PATH}/{folder_name}/{folder_name}.tar.gz"):
                    self.folder_type_dict[folder_name] = "tar.gz"
                else:
                    self.folder_type_dict[folder_name] = "folder"
            try:
                info = self.oc.file_info(f"/{folder_name}/{folder_name}.tar.gz")
                size = info.attributes["{DAV:}getcontentlength"]
                folder_token_flag[folder_name] = True
                logging.info(f"index={idx} /{folder_name}/{folder_name}.tar.gz => {size} bytes")
                accept_flag += 1
            except Exception:
                folder_token_flag[folder_name] = False

        success, data = read_json(shareID_file)
        if success:
            self.shareID = data

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
            success, output = find_key(mc["eBlocBroker"]["shareID"], folder_name)
            if success:
                self.shareID[folder_name] = {
                    "shareID": output["shareID"],
                    "share_token": output["share_token"],
                }
                mongodb_accept_flag += 1

            if success or (folder_token_flag[folder_name] and bool(self.shareID)):
                accept_flag += 1
            else:
                logging.info("Searching share tokens for the related source code folder.")
                for idx in range(len(share_list) - 1, -1, -1):
                    # Starts iterating from last item to the first one
                    input_folder_name = share_list[idx]["name"]
                    # Removes '/' on the beginning of the string
                    input_folder_name = input_folder_name[1:]
                    share_id = share_list[idx]["id"]
                    # inputOwner = share_list[i]['owner']
                    input_user = f"{share_list[idx]['user']}@b2drop.eudat.eu"
                    if input_folder_name == folder_name and input_user == f_id:
                        self.share_token = str(share_list[idx]["share_token"])
                        self.shareID[folder_name] = {
                            "shareID": int(share_id),
                            "share_token": self.share_token,
                        }
                        # Adding into mongodb for future usage
                        success = add_item_share_id(folder_name, share_id, self.share_token)
                        if success:
                            logging.info("Successfull added into mongodb")
                        else:
                            logging.error("E: Something is wrong, Not added into mongodb")
                        logging.info(f"Found. Name={folder_name} | ShareID={share_id} | share_token={self.share_token}")
                        self.oc.accept_remote_share(int(share_id))
                        logging.info("shareID is accepted.")
                        accept_flag += 1
                        break
            if accept_flag is len(self.source_code_hashes):
                break
        else:
            if mongodb_accept_flag is len(self.source_code_hashes):
                logging.info("Shared token a lready exists on mongodb")
            else:
                logging.error(f"E: Couldn't find a shared file. Found ones are: {self.shareID}")
                return False

        if bool(self.shareID):
            with open(shareID_file, "w") as f:
                json.dump(self.shareID, f)
        else:
            logging.error("Something is wrong. shareID is {}.")
            return False

        size_to_download = 0
        for source_code_hash_text in self.source_code_hashes_to_process:
            folder_name = source_code_hash_text
            if not self.is_already_cached[folder_name]:
                info = self.oc.file_info(f"/{folder_name}/{folder_name}.tar.gz")
                size_to_download += int(info.attributes["{DAV:}getcontentlength"])

        logging.info(f"Total size to download={size_to_download}")
        return True, byte_to_mb(size_to_download)

    def run(self) -> bool:
        # TODO: refund check
        log(f"New job has been received. EUDAT call | {time.ctime()}", "blue")

        success, provider_info = get_provider_info(self.logged_job.args["provider"])
        success, self.dataTransferIn_used = self.eudat_get_share_token(provider_info["fID"])
        if not success:
            return False

        if self.dataTransferIn_used > self.dataTransferIn_requested:
            logging.error(
                "E: Requested size to download the source code and data files is greater that the given amount."
            )
            return self.complete_refund()

        success = self.cache_wrapper()
        if not success:
            return False

        for folder_name in self.source_code_hashes_to_process:
            if self.folder_type_dict[folder_name] == "tar.gz":
                # Untar cached tar file into private directory
                tar_to_extract = self.tar_downloaded_path[folder_name]
                if self.job_key == folder_name:
                    target = self.results_folder
                else:
                    target = f"{self.results_data_folder}/{folder_name}"
                    create_dir(target)

                success, output = self.untar(tar_to_extract, target)
                if output:
                    logging.info(output)

        link = Link(self.results_data_folder, self.results_data_link)
        link.link_folders()
        if not os.path.isfile(f"{self.results_folder}/run.sh"):
            logging.error(f"{self.results_folder}/run.sh file does not exist")
            return False

        logging.info(f"dataTransferIn_requested={self.dataTransferIn_requested} MB")

        for folder_name in self.source_code_hashes_to_process:
            try:
                self.shareID[folder_name]["share_token"]
            except KeyError:
                success, output = find_key(mc["eBlocBroker"]["shareID"], folder_name)
                if not success:
                    logging.error(f"E: shareID cannot detected from key: {self.job_key}")
                return False

        return self.sbatch_call()
