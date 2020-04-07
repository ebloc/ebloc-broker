#!/usr/bin/env python3

import os
import subprocess
import time

import libs.git as git
import libs.ipfs as ipfs
from config import bp, logging  # noqa: F401
from lib import (
    CacheType,
    StorageID,
    calculate_folder_size,
    is_ipfs_hash_exists,
    is_ipfs_hash_locally_cached,
    is_ipfs_running,
    log,
    run_command,
    silent_remove,
)
from settings import init_env
from storage_class import Storage
from utils import byte_to_mb, bytes32_to_ipfs, create_dir


class IpfsClass(Storage):
    def __init__(self, logged_job, jobInfo, requester_id, is_already_cached, oc=None):
        super(self.__class__, self).__init__(logged_job, jobInfo, requester_id, is_already_cached, oc)
        # cache_type is should be public on IPFS
        self.cache_type = CacheType.PUBLIC.value
        self.ipfs_hashes = []
        self.cumulative_sizes = {}

    def decrypt_using_minilock(self, ipfs_hash):
        env = init_env()
        with open(f"{env.LOG_PATH}/private/miniLockPassword.txt", "r") as content_file:
            passW = content_file.read().strip()

        cmd = [
            "mlck",
            "decrypt",
            "-f",
            f"{self.results_folder}/ipfsHash",
            f"--passphrase={passW}",
            f"--output-file={self.results_folder}/output.tar.gz",
        ]
        passW = None
        success, output = run_command(cmd)
        cmd = None
        logging.info(f"mlck decrypt success={success}")
        tar_file = f"{self.results_folder}/output.tar.gz"
        subprocess.run(["tar", "-xvf", tar_file, "-C", self.results_folder])
        silent_remove(f"{self.results_folder}/{ipfs_hash}")
        silent_remove(f"{self.results_folder}/output.tar.gz")

    def check_ipfs(self, ipfs_hash) -> bool:
        success, ipfs_stat, cumulative_size = is_ipfs_hash_exists(ipfs_hash, attempt_count=1)
        self.ipfs_hashes.append(ipfs_hash)
        self.cumulative_sizes[self.job_key] = cumulative_size
        data_size_mb = byte_to_mb(cumulative_size)
        logging.info(f"dataTransferOut={data_size_mb} MB | Rounded={int(data_size_mb)} MB")

        if not success or not ("CumulativeSize" in ipfs_stat):
            logging.error("E: Markle not found! Timeout for the IPFS object stat retrieve.")
            return False
        return True

    def run(self):
        log(f"[{time.ctime()}] New job has been received through IPFS", "blue")
        if not is_ipfs_running():
            return False

        logging.info(f"is_ipfs_hash_locally_cached={is_ipfs_hash_locally_cached(self.job_key)}")

        if not os.path.isdir(self.results_folder):
            os.makedirs(self.results_folder)

        silent_remove(f"{self.results_folder}/{self.job_key}")
        if not self.check_ipfs(self.job_key):
            return False

        for source_code_hash in self.source_code_hashes:
            ipfs_hash = bytes32_to_ipfs(source_code_hash)
            if ipfs_hash not in self.ipfs_hashes:
                # job_key as data hash already may added to the list
                success = self.check_ipfs(ipfs_hash)
                if not success:
                    return False

        initial_folder_size = calculate_folder_size(self.results_folder)
        for idx, ipfs_hash in enumerate(self.ipfs_hashes):
            # Here scripts knows that provided IPFS hashes exists
            logging.info(f"Attempting to get IPFS file: {ipfs_hash}")
            is_hashed = False
            if is_ipfs_hash_locally_cached(ipfs_hash):
                is_hashed = True
                log(f"=> IPFS file {ipfs_hash} is already cached.", "blue")

            if idx == 0:
                target = self.results_folder
            else:
                target = f"{self.results_data_folder}/{ipfs_hash}"
                create_dir(target)

            ipfs.get_hash(ipfs_hash, target, False)
            if not git.initialize_check(target):
                return False

            if self.cloudStorageID == StorageID.IPFS_MINILOCK.value:
                self.decrypt_using_minilock(ipfs_hash)

            if not is_hashed:
                folder_size = calculate_folder_size(self.results_folder)
                self.dataTransferIn_used += folder_size - initial_folder_size
                initial_folder_size = folder_size
                # self.dataTransferIn_used += byte_to_mb(cumulative_size)

            if idx == 0 and not os.path.isfile(f"{self.results_folder}/run.sh"):
                logging.error("run.sh file does not exist")
                return False

        logging.info(f"dataTransferIn={self.dataTransferIn_used} MB | Rounded={int(self.dataTransferIn_used)} MB")
        return self.sbatch_call()
