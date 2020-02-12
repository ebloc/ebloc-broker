#!/usr/bin/env python3


import os
import subprocess
import sys
import time
import traceback

import lib
from config import logging
from contractCalls.get_provider_info import get_provider_info
from lib import (EBLOCPATH, PROGRAM_PATH, CacheType, convert_byte_to_mb, execute_shell_command, log,
                 sbatchCall, silentremove)


class GdriveClass:
    def __init__(self, loggedJob, jobInfo, requesterID, is_already_cached):
        self.shareToken = "-1"  # Constant value for Gdrive
        self.requesterID = requesterID
        self.jobInfo = jobInfo
        self.loggedJob = loggedJob
        self.job_key = self.loggedJob.args["jobKey"]
        self.index = self.loggedJob.args["index"]
        self.jobID = 0
        self.cache_type = loggedJob.args["cacheType"]
        self.dataTransferIn = 0
        self.dataTransferIn = jobInfo[0]["dataTransferIn"]
        self.is_already_cached = is_already_cached
        self.results_folder_prev = ""
        self.results_folder = ""
        self.source_code_hash_list = loggedJob.args["sourceCodeHash"]
        self.job_key_list = []
        self.md5sum_dict = {}

    def cache(self, _id, folder_name, source_code_hash, folder_type, key, job_key_flag):
        is_cached = False
        if (
            self.cache_type[_id] == CacheType.PRIVATE.value
        ):  # First checking does is already exist under public cache directory
            cache_folder = f"{PROGRAM_PATH}/{self.requesterID}/cache"
            if not os.path.isdir(cache_folder):  # If folder does not exist
                os.makedirs(cache_folder)

            cached_tar_file = f"{cache_folder}/{folder_name}"
            if folder_type == "gzip":
                if os.path.isfile(cached_tar_file):
                    is_cached = True
                    res = (
                        subprocess.check_output(["bash", f"{EBLOCPATH}/scripts/generateMD5sum.sh", cached_tar_file])
                        .decode("utf-8")
                        .strip()
                    )

                    if res != self.md5sum_dict[key]:
                        logging.error("E: File's md5sum does not match with its orignal md5sum value")
                        return False, None

                    if (
                        res == source_code_hash
                    ):  # Checking is already downloaded folder's hash matches with the given hash
                        logging.info(f"{folder_name} is already cached within private cache directory...")
                        self.cache_type[_id] = CacheType.PRIVATE.value
                        return True, None
            elif folder_type == "folder":
                tar_folder_path = f"{cache_folder}/{folder_name}"
                tar_file_path = f"{tar_folder_path}/{source_code_hash}.tar.gz"
                if os.path.isfile(tar_file_path):
                    is_cached = True
                    res = (
                        subprocess.check_output(["bash", f"{EBLOCPATH}/scripts/generateMD5sum.sh", tar_file_path])
                        .decode("utf-8")
                        .strip()
                    )
                elif os.path.isdir(tar_folder_path):
                    is_cached = True
                    res = (
                        subprocess.check_output(["bash", f"{EBLOCPATH}/scripts/generateMD5sum.sh", tar_folder_path])
                        .decode("utf-8")
                        .strip()
                    )

                if res == source_code_hash:
                    # Checking is already downloaded folder's hash matches with the given hash
                    logging.info(f"{folder_name} is already cached within the private cache directory...")
                    self.cache_type[_id] = CacheType.PRIVATE.value
                    return True, None

        if self.cache_type[_id] == CacheType.PUBLIC.value:
            cache_folder = f"{PROGRAM_PATH}/cache"
            if not os.path.isdir(cache_folder):  # If folder does not exist
                os.makedirs(cache_folder)

            cached_tar_file = f"{cache_folder}/{folder_name}"
            if folder_type == "gzip":
                if not os.path.isfile(cached_tar_file):
                    if not self.gdrive_download_folder(folder_name, folder_type, key):
                        return False, None

                    if job_key_flag and not lib.isRunExistInTar(cached_tar_file):
                        silentremove(cached_tar_file)
                        return False, None
                else:
                    res = (
                        subprocess.check_output(["bash", f"{lib.EBLOCPATH}/scripts/generateMD5sum.sh", cached_tar_file])
                        .decode("utf-8")
                        .strip()
                    )
                    if (
                        res == source_code_hash
                    ):  # Checking is already downloaded folder's hash matches with the given hash
                        logging.info(f"{folder_name} is already cached within public cache directory...")
                    else:
                        if not self.gdrive_download_folder(folder_name, folder_type, key):
                            return False, None
            elif folder_type == "folder":
                if os.path.isfile(f"{cache_folder}/{folder_name}/{source_code_hash}.tar.gz"):
                    tar_file = f"{cache_folder}/{folder_name}/{source_code_hash}.tar.gz"
                    res = (
                        subprocess.check_output(["bash", f"{lib.EBLOCPATH}/scripts/generateMD5sum.sh", tar_file])
                        .decode("utf-8")
                        .strip()
                    )
                    if (
                        res == source_code_hash
                    ):  # Checking is already downloaded folder's hash matches with the given hash
                        logging.info(f"{folder_name} is already cached within public cache directory...")
                    else:
                        if not self.gdrive_download_folder(folder_name, folder_type, key):
                            return False, None
                else:
                    if not self.gdrive_download_folder(folder_name, folder_type, key):
                        return False, None

        return True, None

    def gdrive_download_folder(self, folder_name, folder_type, key) -> bool:
        logging.info(f"Downloading => {key}" f"\n" f"Path to download => {self.results_folder_prev}")

        if folder_type == "folder":
            # cmd: gdrive download --recursive $key --force --path $results_folder_prev  # Gets the source  %TODOTODO
            is_status, res = lib.subprocessCallAttempt(
                ["gdrive", "download", "--recursive", key, "--force", "--path", self.results_folder_prev], 10
            )
            if not is_status:
                return False

            if not os.path.isdir(f"{self.results_folder_prev}/{folder_name}"):
                # Check before move operation
                logging.error("E: Folder is not downloaded successfully.")
                return False
            else:
                p1 = subprocess.Popen(
                    ["du", "-sb", f"{self.results_folder_prev}/{folder_name}"], stdout=subprocess.PIPE
                )
                p2 = subprocess.Popen(["awk", "{print $1}"], stdin=p1.stdout, stdout=subprocess.PIPE)
                p1.stdout.close()
                self.dataTransferIn = convert_byte_to_mb(
                    p2.communicate()[0].decode("utf-8").strip()
                )  # Retunrs downloaded files size in bytes
                logging.info(f"dataTransferIn={self.dataTransferIn} MB | Rounded={int(self.dataTransferIn)} MB")
        else:
            # cmd: gdrive download $key --force --path $results_folder_prev
            is_status, res = lib.subprocessCallAttempt(
                ["gdrive", "download", key, "--force", "--path", self.results_folder_prev], 10
            )
            if not is_status:
                return False

            if not os.path.isfile(f"{self.results_folder_prev}/{folder_name}"):
                logging.error("E: File is not downloaded successfully.")
                return False
            else:
                p1 = subprocess.Popen(
                    ["ls", "-ln", f"{self.results_folder_prev}/{folder_name}"], stdout=subprocess.PIPE
                )
                p2 = subprocess.Popen(["awk", "{print $5}"], stdin=p1.stdout, stdout=subprocess.PIPE)
                p1.stdout.close()
                # Returns downloaded files size in bytes
                self.dataTransferIn = lib.convert_byte_to_mb(p2.communicate()[0].decode("utf-8").strip())
                logging.info(f"dataTransferIn={self.dataTransferIn} MB | Rounded={int(self.dataTransferIn)} MB")

        return True

    def get_data_init(self, _id, key, job_key_flag=False):
        used_dataTransferIn = 0
        # cmd: gdrive info $key -c $GDRIVE_METADATA # stored for both pipes otherwise its read and lost
        is_status, gdriveInfo = lib.subprocessCallAttempt(
            ["gdrive", "info", "--bytes", key, "-c", lib.GDRIVE_METADATA], 10
        )
        if not is_status:
            return False

        mime_type = lib.getGdriveFileInfo(gdriveInfo, "Mime")
        folder_name = lib.getGdriveFileInfo(gdriveInfo, "Name")
        logging.info(f"mime_type={mime_type}")

        if job_key_flag:
            # key for the sourceCode tar.gz file is obtained
            is_status, used_dataTransferIn, self.job_key_list, key = lib.gdrive_size(
                key,
                mime_type,
                folder_name,
                gdriveInfo,
                self.results_folder_prev,
                self.source_code_hash_list,
                self.is_already_cached,
            )

        if not is_status:
            return False

        return mime_type, folder_name, used_dataTransferIn

    def get_data(self, key, _id, job_key_flag=False):
        mime_type, folder_name, used_dataTransferIn = self.get_data_init(_id, key, job_key_flag)
        if job_key_flag:
            if used_dataTransferIn > self.dataTransferIn:
                logging.error(
                    "E: requested size to download the sourceCode and datafiles is greater that the given amount."
                )
                # TODO: full refund
                return False

            is_status, gdriveInfo = lib.subprocessCallAttempt(
                ["gdrive", "info", "--bytes", key, "-c", lib.GDRIVE_METADATA], 10
            )
            if not is_status:
                return False

            mime_type = lib.getGdriveFileInfo(gdriveInfo, "Mime")
            folder_name = lib.getGdriveFileInfo(gdriveInfo, "Name")

        source_code_hash = folder_name.replace(".tar.gz", "")  # folder is already stored by its source_code_hash
        logging.info(f"folder_name={folder_name}")
        logging.info(f"mime_type={mime_type}")

        if "gzip" in mime_type:
            is_status, gdriveInfo = lib.subprocessCallAttempt(
                ["gdrive", "info", "--bytes", key, "-c", lib.GDRIVE_METADATA], 10
            )
            if not is_status:
                return False

            source_code_hash = lib.getMd5sum(gdriveInfo)  # if it is gzip obtained from the {gdrive info key}
            self.md5sum_dict[key] = source_code_hash
            logging.info(f"md5sum={self.md5sum_dict[key]}")

        if "gzip" in mime_type:
            # Recieved job is in folder tar.gz
            is_status, ipfs_hash = self.cache(_id, folder_name, source_code_hash, "gzip", key, job_key_flag)
            if not is_status:
                return False

            command = ["tar", "-xf", f"{cache_folder}/{folder_name}", "--strip-components=1", "-C", self.results_folder]
            is_status, result = execute_shell_command(command, None, True)
            """
            if job_key_flag:
            if not os.path.isfile(cache_folder + '/' + folder_name + '/run.sh'):
                return False, None
            """
        elif "folder" in mime_type:
            # Recieved job is in folder format
            is_status, ipfs_hash = self.cache(_id, folder_name, source_code_hash, "folder", key, job_key_flag)
            if not is_status:
                return False

            command = [
                "rsync",
                "-avq",
                "--partial-dir",
                "--omit-dir-times",
                f"{cache_folder}/{folder_name}/",
                self.results_folder,
            ]
            is_status, result = execute_shell_command(command, None, True)
            if os.path.isfile(f"{self.results_folder}/{folder_name}.tar.gz"):
                command = [
                    "tar",
                    "-xf",
                    f"{self.results_folder}/{folder_name}.tar.gz",
                    "--strip-components=1",
                    "-C",
                    self.results_folder,
                ]
                is_status, result = execute_shell_command(command, None, True)
                silentremove(f"{self.results_folder}/{folder_name}.tar.gz")
        else:
            return False

    def run(self) -> bool:
        log(f"=> New job has been received. Googe Drive call |{time.ctime()}", "blue")
        self.results_folder_prev = f"{PROGRAM_PATH}/{self.requesterID}/{self.job_key}_{self.index}"
        self.results_folder = f"{self.results_folder_prev}/JOB_TO_RUN"

        is_status, provider_info = get_provider_info(self.loggedJob.args["provider"])

        if not os.path.isdir(self.results_folder_prev):
            # If folder does not exist
            os.makedirs(self.results_folder_prev)
            os.makedirs(self.results_folder)

        if not os.path.isdir(self.results_folder):
            os.makedirs(self.results_folder)
            self.get_data(self.job_key, 0, True)
        else:
            self.get_data_init(0, self.job_key, True)

        for i in range(0, len(self.job_key_list)):
            key = self.job_key_list[i]
            self.get_data(key, i)

        sys.exit()
        try:
            sbatchCall(
                self.loggedJob,
                self.shareToken,
                self.requesterID,
                self.results_folder,
                self.results_folder_prev,
                self.dataTransferIn,
                self.source_code_hash_list,
                self.jobInfo,
            )
        except Exception:
            logging.error(f"E: Failed to call sbatchCall() function.\n{traceback.format_exc()}")
            return False

        return True


"""
        elif self.cache_type[_id] == lib.CacheType.IPFS.value:
            log("Adding from google drive mount point into IPFS...", "blue")
            if folder_type == "gzip":
                tar_file = lib.GDRIVE_CLOUD_PATH + "/.shared/" + folder_name
                if not os.path.isfile(tar_file):
                    # TODO: It takes 3-5 minutes for shared folder/file to show up on the .shared folder
                    logging.error("E: Requested file does not exit on mounted folder. PATH=" + tar_file)
                    return False, None
                ipfs_hash = subprocess.check_output(["ipfs", "add", tar_file]).decode("utf-8").strip()
            elif folder_type == "folder":
                folder_path = f"{lib.GDRIVE_CLOUD_PATH}/.shared/{folder_name}"
                if not os.path.isdir(folder_path):
                    logging.error(f"E: Requested folder does not exit on mounted folder. PATH={folder_path}")
                    return False, None

                ipfs_hash = subprocess.check_output(["ipfs", "add", "-r", folder_path]).decode("utf-8").strip()
                ipfs_hash = ipfs_hash.splitlines()
                ipfs_hash = ipfs_hash[
                    int(len(ipfs_hash) - 1)
                ]  # Last line of ipfs hash output is obtained which has the root folder's hash
            return True, ipfs_hash.split()[1]
"""

"""
            elif 'zip' in mime_type:  # Recieved job is in zip format
                is_status, ipfs_hash = cache(requesterID, results_folder_prev, folder_name, source_code_hash, 'zip', key, _id, job_key_flag)
                if not is_status:
                    return False

                # cmd: unzip -o $results_folder_prev/$folder_name -d $results_folder
                command = ['unzip', '-o', results_folder_prev + '/' + folder_name, '-d', results_folder]
                is_status, result = execute_shell_command(command, None, True)
                silentremove(results_folder_prev + '/' + folder_name)
            """
""" Gdrive => IPFS no need.
        elif cacheType == lib.CacheType.IPFS.value:
            if 'folder' in mime_type:
                is_status, ipfs_hash = cache(requesterID, results_folder_prev, folder_name, source_code_hash, 'folder', key, _id, job_key_flag)
                if not is_status:
                    return False

                if ipfs_hash is None:
                    log('E: Requested IPFS hash does not exist.')
                    return False


                log('Reading from IPFS hash=' + ipfs_hash)
                # Copy from cached IPFS folder into user's path
                command = ['ipfs', 'get', ipfs_hash, '-o', results_folder]
                is_status, result = execute_shell_command(command, None, True)
            elif 'gzip' in mime_type:
                is_status, ipfs_hash = cache(requesterID, results_folder_prev, folder_name, source_code_hash, 'gzip', key, _id, job_key_flag)
                if not is_status:
                    return False

                log('Reading from IPFS hash=' + ipfs_hash)
                command = ['tar', '-xf', '/ipfs/' + ipfs_hash, '--strip-components=1', '-C', results_folder]
                is_status, result = execute_shell_command(command, None, True)
"""
