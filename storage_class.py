import os
import subprocess
import traceback

from config import logging
from contractCalls.refund import refund
from lib import PROGRAM_PATH, CacheType, _sbatch_call, log, run_command
from utils import create_dir, generate_md5sum


class BaseClass(object):
    def whoami(self):
        return type(self).__name__


class Storage(BaseClass):
    def __init__(self, logged_job, job_info, requesterID, is_already_cached, oc=None) -> None:
        self.requesterID = requesterID
        self.job_info = job_info
        self.logged_job = logged_job
        self.job_key = self.logged_job.args["jobKey"]
        self.index = self.logged_job.args["index"]
        self.job_id = 0
        self.cache_type = logged_job.args["cacheType"]
        self.dataTransferIn_requested = job_info[0]["dataTransferIn"]
        self.dataTransferIn_used = 0
        self.is_already_cached = is_already_cached
        self.source_code_hashes = logged_job.args["sourceCodeHash"]
        self.job_key_list = []
        self.md5sum_dict = {}
        self.folder_path_to_download = {}
        self.oc = oc
        self.cloudStorageID = logged_job.args["cloudStorageID"]
        self.results_folder_prev = f"{PROGRAM_PATH}/{self.requesterID}/{self.job_key}_{self.index}"
        self.results_folder = f"{self.results_folder_prev}/JOB_TO_RUN"
        self.results_data_folder = f"{self.results_folder_prev}/data"
        self.results_data_link = f"{self.results_folder_prev}/data_link"
        self.private_dir = f"{PROGRAM_PATH}/{requesterID}/cache"
        self.public_dir = f"{PROGRAM_PATH}/cache"
        self.folder_type_dict = {}

        create_dir(self.private_dir)
        create_dir(self.public_dir)
        create_dir(self.results_folder)
        create_dir(self.results_data_folder)
        create_dir(self.results_data_link)

    def complete_refund(self) -> bool:
        """Complete refund back to requester"""
        success, output = refund(
            self.logged_job.args["provider"],
            self.PROVIDER_ID,
            self.job_key,
            self.index,
            self.job_id,
            self.source_code_hashes,
        )
        if not success:
            logging.error(output)
        else:
            logging.info(f"refund()_tx_hash={output}")

        return success

    def is_md5sum_matches(self, path, name, id, folder_type, cache_type) -> bool:
        output = generate_md5sum(path)
        if output == name:
            # Checking is already downloaded folder's hash matches with the given hash
            if self.whoami() == "EudatClass" and folder_type != "":
                self.folder_type_dict[name] = folder_type

            self.cache_type[id] = cache_type
            if cache_type == CacheType.PUBLIC.value:
                self.folder_path_to_download[name] = self.public_dir
                log(f"=> {name} is already cached under the public directory...", "blue")
            elif cache_type == CacheType.PRIVATE.value:
                self.folder_path_to_download[name] = self.private_dir
                log(
                    f"=> {name} is already cached under the private directory...", "blue",
                )

            return True

        return False

    def is_cached(self, name, id) -> bool:
        success = False
        if self.cache_type[id] == CacheType.PRIVATE.value:
            # First checking does is already exist under public cache directory
            cached_folder = f"{self.public_dir}/{name}"
            cached_tar_file = f"{cached_folder}.tar.gz"

            if not os.path.isfile(cached_tar_file):
                if os.path.isfile(f"{cached_folder}/run.sh"):
                    success = self.is_md5sum_matches(cached_folder, name, id, "folder", CacheType.PUBLIC.value)
            else:
                if self.whoami() == "EudatClass":
                    self.folder_type_dict[name] = "tar.gz"

                success = self.is_md5sum_matches(cached_tar_file, name, id, "", CacheType.PUBLIC.value)
        else:
            # First checking does is already exist under the requesting user's private cache directory
            cached_folder = self.private_dir
            cached_folder = f"{self.private_dir}/{name}"
            cached_tar_file = f"{cached_folder}.tar.gz"

            if not os.path.isfile(cached_tar_file):
                if os.path.isfile(f"{cached_folder}/run.sh"):
                    success = self.is_md5sum_matches(cached_folder, name, id, "folder", CacheType.PRIVATE.value)
            else:
                if self.whoami() == "EudatClass":
                    self.folder_type_dict[name] = "tar.gz"
                success = self.is_md5sum_matches(cached_tar_file, name, id, "", CacheType.PRIVATE.value)

        return success

    def is_run_exists_in_tar(self, tar_path) -> bool:
        try:
            FNULL = open(os.devnull, "w")
            output = (
                subprocess.check_output(["tar", "ztf", tar_path, "--wildcards", "*/run.sh"], stderr=FNULL)
                .decode("utf-8")
                .strip()
            )
            FNULL.close()
            if output.count("/") == 1:
                # Main folder should contain the 'run.sh' file
                logging.info("./run.sh exists under the parent folder")
                return True
            else:
                logging.error("E: run.sh does not exist under the parent folder")
                return False
        except:
            logging.error("E: run.sh does not exist under the parent folder")
            return False

    def untar(self, tar_file, extract_to):
        if os.path.isfile(tar_file):
            cmd = [
                "tar",
                "xfp",  # umask can be ignored by using the -p (--preserve) option
                tar_file,
                "--strip-components=1",
                "-C",
                extract_to,
            ]
            success, output = run_command(cmd, None, True)
            return success, output
        else:
            return False, ""

    def sbatch_call(self) -> bool:
        try:
            _sbatch_call(
                self.logged_job,
                self.requesterID,
                self.results_folder,
                self.results_folder_prev,
                self.dataTransferIn_used,
                self.source_code_hashes,
                self.job_info,
            )
        except Exception:
            logging.error(f"E: Failed to call _sbatch_call() function.\n{traceback.format_exc()}")
            return False

        return True
