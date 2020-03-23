#!/usr/bin/env python3

import os
import subprocess
import time

import lib
from config import logging
from contractCalls.get_provider_info import get_provider_info
from lib import (WHERE, CacheType, calculate_folder_size, echo_grep_awk,
                 is_run_exists_in_tar, log, run_command, silent_remove)
from lib_gdrive import (gdrive_get_file_id, gdrive_size, get_gdrive_file_info,
                        getMd5sum)
from storage_class import Storage
from utils import byte_to_mb, generate_md5sum


class GdriveClass(Storage):
    def __init__(self, logged_job, jobInfo, requesterID, is_already_cached, oc=None):
        super(self.__class__, self).__init__(logged_job, jobInfo, requesterID, is_already_cached, oc)

    def assign_folder_path_to_download(self, id, source_code_hash, path):
        if self.cache_type[id] == CacheType.PUBLIC.value:
            self.folder_path_to_download[source_code_hash] = path
        elif self.cache_type[id] == CacheType.PRIVATE.value:
            self.folder_path_to_download[source_code_hash] = self.private_dir

    def cache(self, id, name, source_code_hash, key, job_key_flag):
        if id == 0:
            if self.folder_type_dict[source_code_hash] == "folder":
                self.folder_type_dict[source_code_hash] = "gzip"

        if self.cache_type[id] == CacheType.PRIVATE.value:
            # First checking does is already exist under public cache directory
            cache_folder = f"{self.private_dir}"
            cached_tar_file = f"{cache_folder}/{name}"
            if self.folder_type_dict[source_code_hash] == "gzip":
                if os.path.isfile(cached_tar_file):
                    self.is_already_cached[source_code_hash] = True
                    self.assign_folder_path_to_download(id, source_code_hash, cached_tar_file)
                    output = generate_md5sum(cached_tar_file)
                    if output != self.md5sum_dict[key]:
                        logging.error("E: File's md5sum does not match with its orignal md5sum value")
                        return False, None

                    if output == source_code_hash:
                        # Checking is already downloaded folder's hash matches with the given hash
                        log(
                            f"=> {name} is already cached within private cache directory.", "blue",
                        )
                        self.cache_type[id] = CacheType.PRIVATE.value
                        return True, None
                else:
                    if not self.gdrive_download_folder(name, key, source_code_hash, id, cache_folder):
                        return False, None
            elif self.folder_type_dict[source_code_hash] == "folder":
                output = ""
                if os.path.isfile(cached_tar_file):
                    self.is_already_cached[source_code_hash] = True
                    self.assign_folder_path_to_download(id, source_code_hash, cache_folder)
                    output = generate_md5sum(cached_tar_file)
                elif os.path.isdir(cache_folder):
                    self.is_already_cached[source_code_hash] = True
                    self.folder_path_to_download[source_code_hash] = cache_folder
                    output = generate_md5sum(cache_folder)

                if output == source_code_hash:
                    # Checking is already downloaded folder's hash matches with the given hash
                    log(
                        f"=> {name} is already cached within the private cache directory.", "blue",
                    )
                    self.cache_type[id] = CacheType.PRIVATE.value
                    return True, None
                else:
                    if not self.gdrive_download_folder(name, key, source_code_hash, id, cache_folder):
                        return False, None
        elif self.cache_type[id] == CacheType.PUBLIC.value:
            cache_folder = self.public_dir
            cached_tar_file = f"{cache_folder}/{name}"
            if self.folder_type_dict[source_code_hash] == "gzip":
                if not os.path.isfile(cached_tar_file):
                    if not self.gdrive_download_folder(name, key, source_code_hash, id, cache_folder):
                        return False, None

                    if job_key_flag and not is_run_exists_in_tar(cached_tar_file):
                        silent_remove(cached_tar_file)
                        return False, None
                else:
                    output = generate_md5sum(cached_tar_file)
                    if output == source_code_hash:
                        # Checking is already downloaded folder's hash matches with the given hash
                        self.folder_path_to_download[source_code_hash] = self.public_dir
                        log(
                            f"=> {name} is already cached within public cache directory.", "blue",
                        )
                    else:
                        if not self.gdrive_download_folder(name, key, source_code_hash, id, cache_folder):
                            return False, None
            elif self.folder_type_dict[source_code_hash] == "folder":
                tar_file = f"{cache_folder}/{source_code_hash}/{name}"
                if os.path.isfile(tar_file):
                    output = generate_md5sum(tar_file)
                    if output == source_code_hash:
                        # Checking is already downloaded folder's hash matches with the given hash
                        self.folder_path_to_download[source_code_hash] = self.public_dir
                        log(
                            f"=> {name} is already cached within public cache directory.", "blue",
                        )
                    else:
                        if not self.gdrive_download_folder(
                            name, key, source_code_hash, id, f"{self.public_dir}/{name}"
                        ):
                            return False, None
                else:
                    if not self.gdrive_download_folder(name, key, source_code_hash, id, f"{self.public_dir}/{name}"):
                        return False, None

        return True, None

    def gdrive_download_folder(self, name, key, source_code_hash, id, cache_folder) -> bool:
        log(f"Called from {WHERE(1)}", "blue")
        success = self.is_cached(source_code_hash, id)
        if success:
            return True

        if not self.is_already_cached[source_code_hash] and self.jobInfo[0]["storageDuration"][id] == 0:
            log("Downloaded as temporary data file", "yellow")
            self.folder_path_to_download[source_code_hash] = self.results_folder_prev
        else:
            self.folder_path_to_download[source_code_hash] = cache_folder
            # self.assign_folder_path_to_download(id, source_code_hash, cache_folder)

        logging.info(f"Downloading => {key}\n Path to download => {self.folder_path_to_download[source_code_hash]}")
        if self.folder_type_dict[source_code_hash] == "folder":
            success, output = lib.subprocess_call_attempt(
                [
                    "gdrive",
                    "download",
                    "--recursive",
                    key,
                    "--force",
                    "--path",
                    self.folder_path_to_download[source_code_hash],
                ],
                10,
            )
            if not success:
                return False

            downloaded_folder_path = f"{self.folder_path_to_download[source_code_hash]}/{name}"
            if not os.path.isdir(downloaded_folder_path):
                # Check before move operation
                logging.error(f"E: Folder ({downloaded_folder_path}) is not downloaded successfully.")
                return False
            else:
                self.dataTransferIn = calculate_folder_size(downloaded_folder_path)
                logging.info(f"dataTransferIn={self.dataTransferIn} MB | Rounded={int(self.dataTransferIn)} MB")
        else:
            success, output = lib.subprocess_call_attempt(
                ["gdrive", "download", key, "--force", "--path", self.folder_path_to_download[source_code_hash],], 10,
            )
            if not success:
                return False

            file_path = f"{self.folder_path_to_download[source_code_hash]}/{name}"
            if not os.path.isfile(file_path):
                logging.error(f"E: File {file_path} is not downloaded successfully. [ {WHERE(1)} ]")
                return False
            else:
                p1 = subprocess.Popen(
                    ["ls", "-ln", f"{self.folder_path_to_download[source_code_hash]}/{name}",], stdout=subprocess.PIPE,
                )
                p2 = subprocess.Popen(["awk", "{print $5}"], stdin=p1.stdout, stdout=subprocess.PIPE)
                p1.stdout.close()
                # Returns downloaded files size in bytes
                self.dataTransferIn = byte_to_mb(p2.communicate()[0].decode("utf-8").strip())
                logging.info(f"dataTransferIn={self.dataTransferIn} MB | Rounded={int(self.dataTransferIn)} MB")

        return True

    def get_data_init(self, id, key, job_key_flag=False):
        # cmd: gdrive info $key -c $GDRIVE_METADATA # stored for both pipes otherwise its read and lost
        success, gdriveInfo = lib.subprocess_call_attempt(
            ["gdrive", "info", "--bytes", key, "-c", lib.GDRIVE_METADATA], 10
        )
        if not success:
            return False

        mime_type = get_gdrive_file_info(gdriveInfo, "Mime")
        folder_name = get_gdrive_file_info(gdriveInfo, "Name")
        logging.info(f"mime_type={mime_type}")

        if job_key_flag:
            # key for the sourceCode tar.gz file is obtained
            success, self.dataTransferIn_used, self.job_key_list, key = gdrive_size(
                key,
                mime_type,
                folder_name,
                gdriveInfo,
                self.results_folder_prev,
                self.source_code_hashes,
                self.is_already_cached,
            )

        if not success:
            return False

        return mime_type, folder_name, self.dataTransferIn_used

    def remove_downloaded_file(self, source_code_hash, id, path):
        if not self.is_already_cached[source_code_hash] and self.jobInfo[0]["storageDuration"][id] == 0:
            silent_remove(path)

    def get_data(self, key, id, job_key_flag=False):
        mime_type, name, dataTransferIn_used = self.get_data_init(id, key, job_key_flag)
        if job_key_flag:
            if dataTransferIn_used > self.dataTransferIn:
                logging.error(
                    "E: requested size to download the sourceCode and datafiles is greater that the given amount."
                )
                # TODO: full refund
                return False

            success, gdriveInfo = lib.subprocess_call_attempt(
                ["gdrive", "info", "--bytes", key, "-c", lib.GDRIVE_METADATA], 10
            )
            if not success:
                return False

            mime_type = get_gdrive_file_info(gdriveInfo, "Mime")
            name = get_gdrive_file_info(gdriveInfo, "Name")

        source_code_hash = name.replace(".tar.gz", "")  # folder is already stored by its source_code_hash
        logging.info(f"name={name}")
        logging.info(f"mime_type={mime_type}")

        if id == 0:
            # Source code folder, ignore downloading result-*
            name = f"{name}.tar.gz"
            output = gdrive_get_file_id(key)
            key = echo_grep_awk(output, name, "1")
            mime_type = "gzip"

        if "gzip" in mime_type:
            success, gdriveInfo = lib.subprocess_call_attempt(
                ["gdrive", "info", "--bytes", key, "-c", lib.GDRIVE_METADATA], 10
            )
            if not success:
                return False

            # if it is gzip obtained from the {gdrive info key}
            source_code_hash = getMd5sum(gdriveInfo)
            self.md5sum_dict[key] = source_code_hash
            logging.info(f"md5sum={self.md5sum_dict[key]}")

        if "gzip" in mime_type:
            # Recieved job is in folder tar.gz
            self.folder_type_dict[source_code_hash] = "gzip"
            success, ipfs_hash = self.cache(id, name, source_code_hash, key, job_key_flag)
            if not success:
                return False

            cache_folder = self.folder_path_to_download[source_code_hash]
            success, output = self.untar(f"{cache_folder}/{name}", self.results_folder)
            self.remove_downloaded_file(source_code_hash, id, f"{cache_folder}/{name}")

        elif "folder" in mime_type:
            # Recieved job is in folder format
            self.folder_type_dict[source_code_hash] = "folder"
            success, ipfs_hash = self.cache(id, name, source_code_hash, key, job_key_flag)
            if not success:
                return False

            cache_folder = self.folder_path_to_download[source_code_hash]
            cmd = [
                "rsync",
                "-avq",
                "--partial-dir",
                "--omit-dir-times",
                f"{cache_folder}/{name}/",
                self.results_folder,
            ]
            success, output = run_command(cmd, None, True)
            self.remove_downloaded_file(source_code_hash, id, f"{cache_folder}/{name}/")
            tar_file = f"{self.results_folder}/{name}.tar.gz"
            success, output = self.untar(tar_file, self.results_folder)
            if success:
                silent_remove(tar_file)
        else:
            return False

    def run(self) -> bool:
        log(f"=> New job has been received. Googe Drive call | {time.ctime()}", "blue")
        success, provider_info = get_provider_info(self.logged_job.args["provider"])

        if not os.path.isdir(self.results_folder):
            self.get_data(self.job_key, 0, True)
        else:
            self.get_data_init(0, self.job_key, True)
            self.get_data(self.job_key, 0, True)

        if not os.path.isfile(f"{self.results_folder}/run.sh"):
            logging.error(f"{self.results_folder}/run.sh does not exist")
            return False

        for idx, _key in enumerate(self.job_key_list):
            self.get_data(_key, idx + 1)

        return self.sbatch_call()
