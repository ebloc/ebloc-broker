#!/usr/bin/env python3

import os
import shutil

import libs.git as git
import libs.ipfs as ipfs
from config import bp, logging  # noqa: F401
from lib import CacheType, StorageID, calculate_folder_size, is_ipfs_running, log, run_command, silent_remove
from libs.storage_class import Storage
from settings import init_env
from utils import byte_to_mb, bytes32_to_ipfs, create_dir, get_time


class IpfsClass(Storage):
    def __init__(self, logged_job, jobInfo, requester_id, is_already_cached, oc=None):
        super(self.__class__, self).__init__(logged_job, jobInfo, requester_id, is_already_cached, oc)
        # cache_type is always public on IPFS
        self.cache_type = CacheType.PUBLIC.value
        self.ipfs_hashes = []
        self.cumulative_sizes = {}

    def decrypt_using_minilock(self, minilock_file, extract_target):
        env = init_env()

        with open(f"{env.LOG_PATH}/mini_lock_pass.txt", "r") as content_file:
            _pass = content_file.read().strip()

        tar_file = f"{minilock_file}.tar.gz"
        cmd = [
            "mlck",
            "decrypt",
            "-f",
            minilock_file,
            f"--passphrase={_pass}",
            f"--output-file={tar_file}",
        ]
        _pass = None

        success, output = run_command(cmd)
        if not success:
            silent_remove(minilock_file)
            return False
        try:
            silent_remove(minilock_file)
            logging.info(f"mlck decrypt: SUCCESS")
            run_command(["tar", "-xvf", tar_file, "-C", extract_target, "--strip", "1"])
        except:
            logging.error("E: Could not decrypt the given file")
            raise
        finally:
            cmd = None
            silent_remove(tar_file)

    def check_ipfs(self, ipfs_hash) -> bool:
        success, ipfs_stat, cumulative_size = ipfs.is_hash_exists_online(ipfs_hash, attempt_count=1)
        if not success or not ("CumulativeSize" in ipfs_stat):
            logging.error("E: Markle not found! Timeout for the IPFS object stat retrieve")
            return False

        self.ipfs_hashes.append(ipfs_hash)
        self.cumulative_sizes[self.job_key] = cumulative_size
        data_size_mb = byte_to_mb(cumulative_size)
        logging.info(f"dataTransferOut={data_size_mb} MB | Rounded={int(data_size_mb)} MB")
        return True

    def run(self) -> bool:
        if self.cloudStorageID[0] == StorageID.IPFS.value:
            log(f"[{get_time()}] Job's source code has been sent through IPFS", "cyan")
        else:
            log(f"[{get_time()}] Job's source code has been sent through IPFS_MINILOCK", "cyan")

        if not is_ipfs_running():
            return False

        logging.info(f"is_hash_locally_cached={ipfs.is_hash_locally_cached(self.job_key)}")
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
            # here scripts knows that provided IPFS hashes exists
            is_hashed = False
            logging.info(f"Attempting to get IPFS file: {ipfs_hash}")
            if ipfs.is_hash_locally_cached(ipfs_hash):
                is_hashed = True
                log(f"=> IPFS file {ipfs_hash} is already cached.", "blue")

            if idx == 0:
                target = self.results_folder
            else:
                #  "_" added before the filename in case $ ipfs get <ipfs_hash>
                target = f"{self.results_data_folder}/_{ipfs_hash}"
                create_dir(target)

            is_storage_paid = False  # TODO: should be set before by user input
            ipfs.get(ipfs_hash, target, is_storage_paid)
            if idx > 0:
                shutil.move(target, f"{self.results_data_folder}/{ipfs_hash}")  # unix mv command
                target = f"{self.results_data_folder}/{ipfs_hash}"

            if self.cloudStorageID[idx] == StorageID.IPFS_MINILOCK.value:
                self.decrypt_using_minilock(f"{target}/{ipfs_hash}", target)

            if not git.initialize_check(target):
                return False

            if not is_hashed:
                folder_size = calculate_folder_size(self.results_folder)
                self.dataTransferIn_used += folder_size - initial_folder_size
                initial_folder_size = folder_size
                # self.dataTransferIn_used += byte_to_mb(cumulative_size)

            if idx == 0 and not self.check_run_sh():
                # TODO: refund
                success = self.complete_refund()
                return False

        logging.info(f"dataTransferIn={self.dataTransferIn_used} MB | Rounded={int(self.dataTransferIn_used)} MB")
        return self.sbatch_call()
