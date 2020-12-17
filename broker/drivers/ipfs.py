#!/usr/bin/env python3

import os
import shutil
import time

from broker import cfg
from broker._utils._log import br
from broker._utils.tools import mkdir
from broker.config import ThreadFilter, env, logging, setup_logger  # noqa: F401
from broker.drivers.storage_class import Storage
from broker.lib import calculate_folder_size
from broker.libs import _git
from broker.utils import CacheType, StorageID, _remove, byte_to_mb, bytes32_to_ipfs, get_time, is_ipfs_on, log


class IpfsClass(Storage):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # cache_type is always public on IPFS
        self.cache_type = CacheType.PUBLIC
        self.ipfs_hashes = []
        self.cumulative_sizes = {}

    def check_ipfs(self, ipfs_hash) -> None:
        try:
            ipfs_stat, cumulative_size = cfg.ipfs.is_hash_exists_online(ipfs_hash)
            if "CumulativeSize" not in ipfs_stat:
                raise Exception("E: Markle not found! Timeout for the IPFS object stat retrieve.")
        except Exception as e:
            raise e

        self.ipfs_hashes.append(ipfs_hash)
        self.cumulative_sizes[self.job_key] = cumulative_size
        data_size_mb = byte_to_mb(cumulative_size)
        logging.info(f"data_transfer_out={data_size_mb} MB | Rounded={int(data_size_mb)} MB")

    def run(self) -> bool:
        self.start_time = time.time()
        if env.IS_THREADING_ENABLED:
            self.thread_log_setup()

        log(f"{br(get_time())} Job's source code has been sent through ", "bold cyan", end="")
        if self.cloudStorageID[0] == StorageID.IPFS:
            log("IPFS ", "bold cyan")
        else:
            log("IPFS_GPG ", "bold cyan")

        if not is_ipfs_on():
            return False

        log(f"==> is_hash_locally_cached={cfg.ipfs.is_hash_locally_cached(self.job_key)}")
        if not os.path.isdir(self.results_folder):
            os.makedirs(self.results_folder)

        _remove(f"{self.results_folder}/{self.job_key}")
        try:
            self.check_ipfs(self.job_key)
        except:
            return False

        for source_code_hash in self.source_code_hashes:
            ipfs_hash = bytes32_to_ipfs(source_code_hash)
            if ipfs_hash not in self.ipfs_hashes:
                # job_key as data hash already may added to the list
                try:
                    self.check_ipfs(ipfs_hash)
                except:
                    return False

        initial_folder_size = calculate_folder_size(self.results_folder)
        for idx, ipfs_hash in enumerate(self.ipfs_hashes):
            # here scripts knows that provided IPFS hashes exists online
            is_hashed = False
            log(f"## Attempting to get IPFS file: {ipfs_hash}...", end="")
            if cfg.ipfs.is_hash_locally_cached(ipfs_hash):
                is_hashed = True
                log("already cached", "bold blue")
            else:
                log()

            if idx == 0:
                target = self.results_folder
            else:
                #  "_" added before the filename in case $ ipfs get <ipfs_hash>
                target = f"{self.results_data_folder}/_{ipfs_hash}"
                mkdir(target)

            is_storage_paid = False  # TODO: should be set before by user input
            cfg.ipfs.get(ipfs_hash, target, is_storage_paid)
            if idx > 0:
                # https://stackoverflow.com/a/31814223/2402577
                dst_filename = os.path.join(self.results_data_folder, os.path.basename(ipfs_hash))
                if os.path.exists(dst_filename):
                    _remove(dst_filename)

                shutil.move(target, dst_filename)
                target = dst_filename

            if self.cloudStorageID[idx] == StorageID.IPFS_GPG:
                cfg.ipfs.decrypt_using_gpg(f"{target}/{ipfs_hash}", target)

            if not _git.initialize_check(target):
                return False

            if not is_hashed:
                folder_size = calculate_folder_size(self.results_folder)
                self.data_transfer_in_to_download_mb += folder_size - initial_folder_size
                initial_folder_size = folder_size

            if idx == 0 and not self.check_run_sh():
                self.complete_refund()
                return False

        log(
            f"data_transfer_in={self.data_transfer_in_to_download_mb} MB |"
            f" rounded={int(self.data_transfer_in_to_download_mb)} MB",
            "bold",
        )
        return self.sbatch_call()
