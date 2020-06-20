import json
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime, timedelta
from shutil import copyfile

import eblocbroker.Contract as Contract
import libs.mongodb as mongodb
import libs.slurm as slurm
import utils
from config import ThreadFilter, env, logging
from lib import log, run
from startup import bp  # noqa: F401
from utils import (
    CacheType,
    Link,
    _colorize_traceback,
    create_dir,
    generate_md5sum,
    is_dir_empty,
    read_json,
    write_to_file,
)


class BaseClass:
    def whoami(self):
        return type(self).__name__


class Storage(BaseClass):
    def __init__(self, logged_job, job_info, requester_id, is_already_cached) -> None:
        self.thread_name = uuid.uuid4().hex  # https://stackoverflow.com/a/44992275/2402577
        self.requester_id = requester_id
        self.job_info = job_info
        self.logged_job = logged_job
        self.job_key = self.logged_job.args["jobKey"]
        self.index = self.logged_job.args["index"]
        self.cores = self.logged_job.args["core"]
        self.execution_durations = self.logged_job.args["executionDuration"]
        self.job_id = 0
        self.cache_type = logged_job.args["cacheType"]
        self.dataTransferIn_requested = job_info[0]["dataTransferIn"]
        self.dataTransferIn_to_download = 0  # size_to_download
        self.is_already_cached = is_already_cached
        self.source_code_hashes = logged_job.args["sourceCodeHash"]
        self.job_key_list = []
        self.md5sum_dict = {}
        self.folder_path_to_download = {}
        self.cloudStorageID = logged_job.args["cloudStorageID"]
        self.results_folder_prev = f"{env.PROGRAM_PATH}/{self.requester_id}/{self.job_key}_{self.index}"
        self.results_folder = f"{self.results_folder_prev}/JOB_TO_RUN"
        self.run_path = f"{self.results_folder}/run.sh"
        self.results_data_folder = f"{self.results_folder_prev}/data"
        self.results_data_link = f"{self.results_folder_prev}/data_link"
        self.private_dir = f"{env.PROGRAM_PATH}/{requester_id}/cache"
        self.public_dir = f"{env.PROGRAM_PATH}/cache"
        self.patch_folder = f"{self.results_folder_prev}/patch"
        self.folder_type_dict = {}
        self.Ebb = Contract.eblocbroker
        self.drivers_log_path = f"{env.LOG_PATH}/drivers_output/{self.job_key}_{self.index}.log"
        self.start_time = None
        self.mc = None
        self.coll = None
        utils.log_files[self.thread_name] = self.drivers_log_path

        create_dir(self.private_dir)
        create_dir(self.public_dir)
        create_dir(self.results_folder)
        create_dir(self.results_data_folder)
        create_dir(self.results_data_link)
        create_dir(self.patch_folder)

    def thread_log_setup(self):
        import threading
        import config

        _log = logging.getLogger()  # root logger
        for hdlr in _log.handlers[:]:  # remove all old handlers
            _log.removeHandler(hdlr)

        # A dedicated per-thread handler
        thread_handler = logging.FileHandler(self.drivers_log_path, "a")
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        thread_handler.setFormatter(formatter)
        # The ThreadFilter makes sure this handler only accepts logrecords that originate
        # in *this* thread, only. It needs the current thread id for this:
        thread_handler.addFilter(ThreadFilter(thread_id=threading.get_ident()))
        config.logging.addHandler(thread_handler)
        time.sleep(0.1)
        # config.logging = logging
        # _log = logging.getLogger()
        # _log.addHandler(thread_handler)
        # config.logging = _log

    def check_already_cached(self, source_code_hash):
        if os.path.isfile(f"{self.private_dir}/{source_code_hash}.tar.gz"):
            log("==> ", "blue", None, is_new_line=False)
            log(f"{source_code_hash} is already cached in {self.private_dir}")
            self.is_already_cached[source_code_hash] = True
        elif os.path.isfile(f"{self.public_dir}/{source_code_hash}.tar.gz"):
            log("==> ", "blue", None, is_new_line=False)
            log(f"{source_code_hash} is already cached in {self.public_dir}")
            self.is_already_cached[source_code_hash] = True

    def complete_refund(self) -> bool:
        """Complete refund back to the requester"""
        try:
            tx_hash = self.Ebb.refund(
                self.logged_job.args["provider"],
                env.PROVIDER_ID,
                self.job_key,
                self.index,
                self.job_id,
                self.cores,
                self.execution_durations,
            )
            log("==> ", "blue", None, is_new_line=False)
            log(f"refund() tx_hash={tx_hash}")
        except:
            _colorize_traceback()
            raise

    def is_md5sum_matches(self, path, name, _id, folder_type, cache_type) -> bool:
        output = generate_md5sum(path)
        if output == name:
            # checking is already downloaded folder's hash matches with the given hash
            if self.whoami() == "EudatClass" and folder_type != "":
                self.folder_type_dict[name] = folder_type

            self.cache_type[_id] = cache_type
            if cache_type == CacheType.PUBLIC:
                self.folder_path_to_download[name] = self.public_dir
                log(f"=> {name} is already cached under the public directory...", "blue")
            elif cache_type == CacheType.PRIVATE:
                self.folder_path_to_download[name] = self.private_dir
                log("==> ", "blue", None, is_new_line=False)
                log(f"{name} is already cached under the private directory")

            return True

        return False

    def is_cached(self, name, _id) -> bool:
        if self.cache_type[_id] == CacheType.PRIVATE:
            # first checking does is already exist under public cache directory
            cached_folder = f"{self.public_dir}/{name}"
            cached_tar_file = f"{cached_folder}.tar.gz"

            if not os.path.isfile(cached_tar_file):
                if os.path.isfile(f"{cached_folder}/run.sh"):
                    return self.is_md5sum_matches(cached_folder, name, _id, "folder", CacheType.PUBLIC)
            else:
                if self.whoami() == "EudatClass":
                    self.folder_type_dict[name] = "tar.gz"

                return self.is_md5sum_matches(cached_tar_file, name, _id, "", CacheType.PUBLIC)
        else:
            # first checking does is already exist under the requesting user's private cache directory
            cached_folder = self.private_dir
            cached_folder = f"{self.private_dir}/{name}"
            cached_tar_file = f"{cached_folder}.tar.gz"

            if not os.path.isfile(cached_tar_file):
                if os.path.isfile(f"{cached_folder}/run.sh"):
                    return self.is_md5sum_matches(cached_folder, name, _id, "folder", CacheType.PRIVATE)
            else:
                if self.whoami() == "EudatClass":
                    self.folder_type_dict[name] = "tar.gz"

                return self.is_md5sum_matches(cached_tar_file, name, _id, "", CacheType.PRIVATE)

        return False

    def is_run_exists_in_tar(self, tar_path) -> bool:
        try:
            output = (
                subprocess.check_output(["tar", "ztf", tar_path, "--wildcards", "*/run.sh"], stderr=subprocess.DEVNULL,)
                .decode("utf-8")
                .strip()
            )
            if output.count("/") == 1:
                # main folder should contain the 'run.sh' file
                logging.info("./run.sh exists under the parent folder")
                return True
            else:
                logging.error("E: run.sh does not exist under the parent folder")
                return False
        except:
            logging.error("E: run.sh does not exist under the parent folder")
            return False

    def check_run_sh(self) -> bool:
        if not os.path.isfile(self.run_path):
            logging.error(f"E: {self.run_path} file does not exist")
            return False
        return True

    def sbatch_call(self) -> bool:
        try:
            link = Link(self.results_data_folder, self.results_data_link)
            link.link_folders()

            # file permission for the requester's foders should be re-set
            path = f"{env.PROGRAM_PATH}/{self.requester_id}"
            run(["sudo", "setfacl", "-R", "-m", f"user:{self.requester_id}:rwx", path])
            run(["sudo", "setfacl", "-R", "-m", f"user:{env.WHOAMI}:rwx", path])

            self._sbatch_call()
        except Exception:
            logging.error("Failed to call _sbatch_call() function.")
            _colorize_traceback()
            raise

    def _sbatch_call(self):
        job_key = self.logged_job.args["jobKey"]
        index = self.logged_job.args["index"]
        main_cloud_storage_id = self.logged_job.args["cloudStorageID"][0]  # 0 indicated maps to sourceCode
        job_info = self.job_info[0]
        job_id = 0  # base job_id for them workflow
        job_block_number = self.logged_job.blockNumber

        # cmd: date --date=1 seconds +%b %d %k:%M:%S %Y
        date = (
            subprocess.check_output(
                ["date", "--date=" + "1 seconds", "+%b %d %k:%M:%S %Y"], env={"LANG": "en_us_88591"},
            )
            .decode("utf-8")
            .strip()
        )
        logging.info(f"Date={date}")
        write_to_file(f"{self.results_folder_prev}/modified_date.txt", date)

        # cmd: echo date | date +%s
        p1 = subprocess.Popen(["echo", date], stdout=subprocess.PIPE)
        p2 = subprocess.Popen(["date", "+%s"], stdin=p1.stdout, stdout=subprocess.PIPE)
        p1.stdout.close()
        timestamp = p2.communicate()[0].decode("utf-8").strip()
        logging.info(f"Timestamp={timestamp}")
        write_to_file(f"{self.results_folder_prev}/timestamp.txt", timestamp)

        logging.info(f"job_received_block_number={job_block_number}")
        # write_to_file(f"{results_folder_prev}/blockNumber.txt", job_block_number)

        logging.info("Adding recevied job into mongodb database.")
        # adding job_key info along with its cacheDuration into mongodb
        mongodb.add_item(
            job_key, self.source_code_hashes, self.requester_id, timestamp, main_cloud_storage_id, job_info,
        )

        # TODO: update as used_dataTransferIn value
        data_transfer_in_json = f"{self.results_folder_prev}/dataTransferIn.json"
        try:
            data = read_json(data_transfer_in_json)
        except:
            data = dict()
            data["dataTransferIn"] = self.dataTransferIn_to_download
            with open(data_transfer_in_json, "w") as outfile:
                json.dump(data, outfile)
            time.sleep(0.25)

        # logging.info(dataTransferIn)
        # seperator character is *
        sbatch_file_path = f"{self.results_folder}/{job_key}*{index}*{job_block_number}.sh"
        copyfile(f"{self.results_folder}/run.sh", sbatch_file_path)

        job_core_num = str(job_info["core"][job_id])
        # client's requested seconds to run his/her job, 1 minute additional given
        execution_time_second = timedelta(seconds=int((job_info["executionDuration"][job_id] + 1) * 60))
        d = datetime(1, 1, 1) + execution_time_second
        time_limit = str(int(d.day) - 1) + "-" + str(d.hour) + ":" + str(d.minute)
        logging.info(f"time_limit={time_limit} | requested_core_num={job_core_num}")
        # give permission to user that will send jobs to Slurm.
        subprocess.check_output(["sudo", "chown", "-R", self.requester_id, self.results_folder])
        for _attempt in range(10):
            try:
                """cmd: # slurm submit job, Real mode -N is used. For Emulator-mode -N use 'sbatch -c'
                sudo su - $requester_id -c "cd $results_folder &&
                sbatch -c$job_core_num $results_folder/${job_key}*${index}.sh --mail-type=ALL
                """
                sub_cmd = f'cd {self.results_folder} && sbatch -N {job_core_num} "{sbatch_file_path}" --mail-type=ALL'
                job_id = run(["sudo", "su", "-", self.requester_id, "-c", sub_cmd])
                time.sleep(1)  # wait 1 second for Slurm idle core to be updated
            except Exception:
                _colorize_traceback()
                slurm.remove_user(self.requester_id)
                slurm.add_user_to_slurm(self.requester_id)
            else:
                break
        else:
            sys.exit(1)

        slurm_job_id = job_id.split()[3]
        logging.info(f"slurm_job_id={slurm_job_id}")
        try:
            run(["scontrol", "update", f"jobid={slurm_job_id}", f"TimeLimit={time_limit}"])
            # subprocess.run(cmd, stderr=subprocess.STDOUT)
        except Exception:
            _colorize_traceback()

        if not slurm_job_id.isdigit():
            logging.error("E: Detects an error on the SLURM side. slurm_job_id is not a digit")
            return False

        return True
