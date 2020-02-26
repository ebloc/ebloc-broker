#!/usr/bin/env python3

import os
import subprocess
import time
from config import logging
from lib import is_ipfs_running, log, silent_remove, get_ipfs_hash, is_ipfs_hash_cached, is_ipfs_hash_exists, convert_bytes32_to_ipfs, calculate_folder_size, StorageID, LOG_PATH, execute_shell_command
from storage_class import Storage


class IpfsClass(Storage):
    def __init__(self, loggedJob, jobInfo, requesterID, is_already_cached, oc=None):
        super(self.__class__, self).__init__(loggedJob, jobInfo, requesterID, is_already_cached, oc)
        # cacheType is should be public on IPFS
        # if the requested file is already cached, it stays as 0
        self.dataTransferIn = 0
        self.share_token = "-1"  # Constant value for ipfs

    def decrypt_using_minilock(self, ipfs_hash):
        with open(f"{LOG_PATH}/private/miniLockPassword.txt", "r") as content_file:
            passW = content_file.read().strip()

        command = [
            "mlck",
            "decrypt",
            "-f",
            f"{self.results_folder}/ipfsHash",
            f"--passphrase={passW}",
            f"--output-file={self.results_folder}/output.tar.gz",
        ]
        passW = None
        status, res = execute_shell_command(command)
        command = None
        logging.info(f"mlck decrypt status={status}")
        tar_file = f"{self.results_folder}/output.tar.gz"
        subprocess.run(["tar", "-xvf", tar_file, "-C", self.results_folder])
        silent_remove(f"{self.results_folder}/{ipfs_hash}")
        silent_remove(f"{self.results_folder}/output.tar.gz")

    def run(self):
        log(f"=> New job has been received. IPFS call | {time.ctime()}", "blue")
        is_ipfs_running()
        cumulative_size_list = []
        ipfs_hash_list = []

        logging.info(f"is_ipfs_hash_cached={is_ipfs_hash_cached(self.job_key)}")

        if not os.path.isdir(self.results_folder):
            os.makedirs(self.results_folder)

        silent_remove(f"{self.results_folder}/{self.job_key}")
        status, ipfs_stat, cumulative_size = is_ipfs_hash_exists(self.job_key, attempt_count=1)
        ipfs_hash_list.append(self.job_key)
        cumulative_size_list.append(cumulative_size)

        if not status or not ("CumulativeSize" in ipfs_stat):
            logging.error("E: Markle not found! Timeout for the IPFS object stat retrieve")
            return False

        for source_code_hash in self.source_code_hashes:
            source_code_ipfs_hash = convert_bytes32_to_ipfs(source_code_hash)
            if source_code_ipfs_hash not in ipfs_hash_list:
                # job_key as data hash already may added to the list
                status, ipfs_stat, cumulative_size = is_ipfs_hash_exists(source_code_ipfs_hash, attempt_count=1)
                cumulative_size_list.append(cumulative_size)
                ipfs_hash_list.append(source_code_ipfs_hash)
                if not status:
                    return False

        initial_size = calculate_folder_size(self.results_folder, "d")
        print(initial_size)

        for ipfs_hash in ipfs_hash_list:  # Here scripts knows that provided IPFS hashes exists
            logging.info(f"Attempting to get IPFS file {ipfs_hash}")
            is_hashed = False
            if is_ipfs_hash_cached(ipfs_hash):
                is_hashed = True
                logging.info(f"=> IPFS file {ipfs_hash} is already cached.")

            get_ipfs_hash(ipfs_hash, self.results_folder, False)
            if self.cloudStorageID == StorageID.IPFS_MINILOCK.value:  # Case for the ipfsMiniLock
                self.decrypt_using_minilock(ipfs_hash)

            if not is_hashed:
                folder_size = calculate_folder_size(self.results_folder, "d")
                self.dataTransferIn += folder_size - initial_size
                initial_size = folder_size
                # dataTransferIn += convert_byte_to_mb(cumulative_size)

            if not os.path.isfile(f"{self.results_folder}/run.sh"):
                logging.error("run.sh file does not exist")
                return False

        logging.info(f"dataTransferIn={self.dataTransferIn} MB | Rounded={int(self.dataTransferIn)} MB")

        if not self.sbatch_call():
            return False

        return True
