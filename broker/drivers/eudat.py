#!/usr/bin/env python3

import json
import os
import sys
import time
from typing import List

import broker.cfg as cfg
import broker.config as config
import broker.eblocbroker.Contract as Contract
from broker.config import env, logging
from broker.drivers.storage_class import Storage
from broker.utils import (
    CacheType,
    _colorize_traceback,
    _remove,
    generate_md5sum,
    get_time,
    log,
    mkdir,
    read_json,
    untar,
)

Ebb: "Contract.Contract" = Contract.EBB()


class EudatClass(Storage):
    def __init__(self, logged_job, jobInfo, requester_id, is_already_cached):
        super().__init__(logged_job, jobInfo, requester_id, is_already_cached)
        self.share_token = None
        self.accept_flag = 0
        self.shareID = {}
        self.tar_downloaded_path = {}
        self.source_code_hashes_to_process: List[str] = []
        for source_code_hash in self.source_code_hashes:
            self.source_code_hashes_to_process.append(cfg.w3.toText(source_code_hash))

        for source_code_hash in self.source_code_hashes_to_process:
            self.check_already_cached(source_code_hash)

    def cache_wrapper(self) -> bool:
        for idx, folder_name in enumerate(self.source_code_hashes_to_process):
            if not self.cache(folder_name, idx):
                return False
        return True

    def search_token(self, f_id, share_list, folder_name):
        logging.info("Searching share tokens for the related source code folder")
        for idx in range(len(share_list) - 1, -1, -1):
            # starts iterating from last item to the first one
            input_folder_name = share_list[idx]["name"]
            # removes '/' on the beginning of the string
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
                # adding into mongoDB for future usage
                if Ebb.mongo_broker.add_item_share_id(folder_name, share_id, self.share_token):
                    logging.info("Added into mongoDB [ SUCCESS ]")
                else:
                    logging.error("E: Something is wrong, Not added into mongoDB")

                log(f"Found. name={folder_name} | share_id={share_id} | share_token={self.share_token}")
                config.oc.accept_remote_share(int(share_id))
                logging.info("share_id is accepted.")
                self.accept_flag += 1
                break

    def cache(self, folder_name, _id) -> bool:
        success = self.is_cached(folder_name, _id)
        cached_folder = ""
        if self.cache_type[_id] == CacheType.PRIVATE:
            # download into private directory at $HOME/.ebloc-broker/cache
            cached_folder = self.private_dir
        elif self.cache_type[_id] == CacheType.PUBLIC:
            cached_folder = self.public_dir

        cached_tar_file = f"{cached_folder}/{folder_name}.tar.gz"
        if success:
            self.folder_type_dict[folder_name] = "tar.gz"
            self.tar_downloaded_path[folder_name] = cached_tar_file
            return True

        if not os.path.isfile(cached_tar_file):
            if os.path.isfile(f"{cached_folder}/{folder_name}.tar.gz"):
                tar_hash = generate_md5sum(f"{cached_folder}/{folder_name}.tar.gz")
                if tar_hash == folder_name:
                    # checking is already downloaded folder's hash matches with the given hash
                    self.folder_type_dict[folder_name] = "folder"
                    log(f"{folder_name} is already cached under the public directory", "blue")
                    return True

                self.folder_type_dict[folder_name] = "tar.gz"
                if not self.eudat_download_folder(cached_folder, folder_name):
                    return False
            else:
                self.folder_type_dict[folder_name] = "tar.gz"
                if not self.eudat_download_folder(cached_folder, folder_name):
                    return False

            if (
                _id == 0
                and self.folder_type_dict[folder_name] == "tar.gz"
                and not self.is_run_exists_in_tar(cached_tar_file)
            ):
                _remove(cached_tar_file)
                return False
        else:
            # Here we already know that its tar.gz file
            self.folder_type_dict[folder_name] = "tar.gz"
            output = generate_md5sum(cached_tar_file)
            if output == folder_name:
                # checking is already downloaded folder's hash matches with the given hash
                log(f"==> {cached_tar_file} is already cached")
                self.tar_downloaded_path[folder_name] = cached_tar_file
                self.folder_type_dict[folder_name] = "tar.gz"
                return True

            if not self.eudat_download_folder(cached_folder, folder_name):
                return False
        return True

    def eudat_download_folder(self, results_folder_prev, folder_name) -> bool:
        # assumes job is sent as .tar.gz file
        cached_tar_file = f"{results_folder_prev}/{folder_name}.tar.gz"
        logging.info(f"Downloading output.zip for:\n{folder_name} => {cached_tar_file}")
        for attempt in range(config.RECONNECT_ATTEMPTS):
            try:
                if config.oc.get_file(f"/{folder_name}/{folder_name}.tar.gz", cached_tar_file):
                    self.tar_downloaded_path[folder_name] = cached_tar_file
                    logging.info("Done")
                else:
                    logging.error(f"E: Something is wrong; oc could not retrieve the file [attempt:{attempt}]")
                    return False
            except Exception:
                logging.error("Failed to download eudat file")
                _colorize_traceback()
                log("Waiting for 5 seconds...")
                time.sleep(5)
            else:
                break
        else:
            self.complete_refund()
            return False

        # TODO: check hash of the downloaded file is correct or not
        return True

    def eudat_get_share_token(self, f_id):
        """Checks already shared or not."""
        folder_token_flag = dict()
        if not os.path.isdir(self.private_dir):
            logging.error(f"{self.private_dir} does not exist")
            raise

        share_id_file = f"{self.private_dir}/{self.job_key}_shareID.json"
        # accept_flag = 0 # TODO: delete it seems unneeded
        for idx, source_code_hash_text in enumerate(self.source_code_hashes_to_process):
            folder_name = source_code_hash_text
            self.folder_type_dict[folder_name] = None
            if os.path.isdir(f"{env.OWNCLOUD_PATH}/{folder_name}"):
                logging.warning(
                    f"Eudat shared folder({folder_name}) is already accepted and exists on the eudat's mounted folder."
                )
                if os.path.isfile(f"{env.OWNLOUD_PATH}/{folder_name}/{folder_name}.tar.gz"):
                    self.folder_type_dict[folder_name] = "tar.gz"
                else:
                    self.folder_type_dict[folder_name] = "folder"

            try:
                info = config.oc.file_info(f"/{folder_name}/{folder_name}.tar.gz")
                logging.info("Shared folder is already accepted")
                size = info.attributes["{DAV:}getcontentlength"]
                folder_token_flag[folder_name] = True
                logging.info(f"index=[{idx}]: /{folder_name}/{folder_name}.tar.gz => {size} bytes")
                # accept_flag += 1  # TODO: delete it seems unneeded
            except Exception:
                logging.warning("E: Shared folder did not accepted yet")
                folder_token_flag[folder_name] = False

        try:  # TODO: pass on template'i ekle
            data = read_json(share_id_file)
            if isinstance(data, dict) and bool(data):
                self.shareID = data
        except:
            pass

        logging.info(f"share_id_dict={self.shareID}")
        for attempt in range(config.RECONNECT_ATTEMPTS):
            try:
                share_list = config.oc.list_open_remote_share()
            except Exception:
                logging.error(f"E: Failed to list_open_remote_share eudat [attempt={attempt}]")
                _colorize_traceback()
                time.sleep(1)
            else:
                break
        else:
            return False

        mongodb_accept_flag = 0
        self.accept_flag = 0
        for source_code_hash_text in self.source_code_hashes_to_process:
            folder_name = source_code_hash_text
            try:
                shared_id = Ebb.mongo_broker.mc["eBlocBroker"]["shareID"]
                output = Ebb.mongo_broker.find_key(shared_id, folder_name)
                self.shareID[folder_name] = {
                    "shareID": output["shareID"],
                    "share_token": output["share_token"],
                }
                mongodb_accept_flag += 1
                self.accept_flag += 1
            except:
                if folder_token_flag[folder_name] and bool(self.shareID):
                    self.accept_flag += 1
                else:
                    self.search_token(f_id, share_list, folder_name)

            if self.accept_flag is len(self.source_code_hashes):
                break
        else:
            if mongodb_accept_flag is len(self.source_code_hashes):
                logging.info("Shared token a lready exists on mongoDB")
            else:
                logging.error(f"E: Could not find a shared file. Found ones are: {self.shareID}")
                raise

        if bool(self.shareID):
            with open(share_id_file, "w") as f:
                json.dump(self.shareID, f)
        else:
            logging.error("Something is wrong. shareID is empty => {}")
            raise

        self.data_transfer_in_to_download = 0  # size_to_download
        for source_code_hash_text in self.source_code_hashes_to_process:
            folder_name = source_code_hash_text
            if not self.is_already_cached[folder_name]:
                info = config.oc.file_info(f"/{folder_name}/{folder_name}.tar.gz")
                self.data_transfer_in_to_download += int(info.attributes["{DAV:}getcontentlength"])
        log(f"Total size to download={self.data_transfer_in_to_download} bytes", "blue")

    def run(self) -> bool:
        self.start_time = time.time()
        if env.IS_THREADING_ENABLED:
            self.thread_log_setup()

        try:
            log(f"Log_path => {self.drivers_log_path}", "green")
            self._run()
            # self.thread_log_setup()
            return True
        except Exception:
            _colorize_traceback(f"{self.job_key}_{self.index}")
            sys.exit(1)
        finally:
            time.sleep(0.25)

    def _run(self) -> bool:
        log(
            f"\n[{get_time()}] New job has been received through EUDAT: {self.job_key} {self.index} "
            "---------------------------------------------------------",
            "cyan",
        )
        log(f"==> Keep track from: tail -f {self.drivers_log_path}")

        # TODO: refund check
        self.coll = Ebb.mongo_broker.mc["eBlocBroker"]["cache"]
        try:
            provider_info = Ebb.get_provider_info(self.logged_job.args["provider"])
            self.eudat_get_share_token(provider_info["f_id"])
        except:
            logging.error("E: could not get the share id")
            _colorize_traceback()
            return False

        if self.data_transfer_in_to_download > self.data_transfer_in_requested:
            log(f"data_transfer_in_to_download={self.data_transfer_in_to_download}")
            log(f"data_transfer_in_requested={self.data_transfer_in_requested}")
            logging.error(
                "E: Requested size to download the source code and data files is greater that the given amount"
            )
            return self.complete_refund()

        if not self.cache_wrapper():
            return False

        for idx, folder_name in enumerate(self.source_code_hashes_to_process):
            if self.folder_type_dict[folder_name] == "tar.gz":
                # untar cached tar file into private directory
                tar_to_extract = self.tar_downloaded_path[folder_name]
                if self.job_key == folder_name:
                    target = self.results_folder
                else:
                    target = f"{self.results_data_folder}/{folder_name}"
                    mkdir(target)

                try:
                    untar(tar_to_extract, target)
                except:
                    return False

                if idx == 0 and not self.check_run_sh():
                    self.complete_refund()
                    return False

        logging.info(f"data_transfer_in_requested={self.data_transfer_in_requested} MB")
        for folder_name in self.source_code_hashes_to_process:
            try:
                self.shareID[folder_name]["share_token"]
            except KeyError:
                try:
                    shared_id = Ebb.mongo_broker.mc["eBlocBroker"]["shareID"]
                    Ebb.mongo_broker.find_key(shared_id, folder_name)
                except:
                    logging.error(f"E: share_id cannot be detected from key: {self.job_key}")
                    return False
        return self.sbatch_call()
