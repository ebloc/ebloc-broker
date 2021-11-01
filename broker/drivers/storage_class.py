#!/usr/bin/env python3

import json
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime, timedelta
from shutil import copyfile
from typing import Dict, List

import broker._utils._log as _log
import broker.cfg as cfg
import broker.libs.slurm as slurm
from broker._utils.tools import mkdir
from broker.config import ThreadFilter, env, logging
from broker.lib import log, run
from broker.libs.slurm import remove_user
from broker.libs.sudo import _run_as_sudo
from broker.libs.user_setup import add_user_to_slurm, give_rwe_access
from broker.utils import CacheType, Link, bytes32_to_ipfs, cd, generate_md5sum, print_tb, read_json, write_to_file


class BaseClass:
    def whoami(self):
        return type(self).__name__


class Storage(BaseClass):
    # def __init__(self, logged_job, job_info, requester_id, is_already_cached) -> None:
    def __init__(self, **kwargs) -> None:
        self.Ebb = cfg.Ebb
        self.thread_name = uuid.uuid4().hex  # https://stackoverflow.com/a/44992275/2402577
        self.requester_id = kwargs.pop("requester_id")
        self.job_info = kwargs.pop("job_info")
        self.logged_job = kwargs.pop("logged_job")
        self.is_already_cached = kwargs.pop("is_already_cached")
        self.job_key = self.logged_job.args["jobKey"]
        self.index = self.logged_job.args["index"]
        self.cores = self.logged_job.args["core"]
        self.run_time = self.logged_job.args["runTime"]
        self.job_id = 0
        self.cache_type = self.logged_job.args["cacheType"]
        self.data_transfer_in_requested = self.job_info[0]["data_transfer_in"]
        self.data_transfer_in_to_download_mb = 0  # total size in MB to download
        self.is_already_cached = self.is_already_cached
        self.source_code_hashes: List[bytes] = self.logged_job.args["sourceCodeHash"]
        self.source_code_hashes_str: List[str] = [bytes32_to_ipfs(_hash) for _hash in self.source_code_hashes]
        self.job_key_list: List[str] = []
        self.md5sum_dict = {}
        self.folder_path_to_download: Dict[str, str] = {}
        self.cloudStorageID = self.logged_job.args["cloudStorageID"]
        self.requester_home = f"{env.PROGRAM_PATH}/{self.requester_id}"
        self.results_folder_prev = f"{self.requester_home}/{self.job_key}_{self.index}"
        self.results_folder = f"{self.results_folder_prev}/JOB_TO_RUN"
        self.run_path = f"{self.results_folder}/run.sh"
        self.results_data_folder = f"{self.results_folder_prev}/data"
        self.results_data_link = f"{self.results_folder_prev}/data_link"
        self.private_dir = f"{self.requester_home}/cache"
        self.public_dir = f"{env.PROGRAM_PATH}/cache"
        self.patch_folder = f"{self.results_folder_prev}/patch"
        self.folder_type_dict: Dict[str, str] = {}
        self.drivers_log_path = f"{env.LOG_PATH}/drivers_output/{self.job_key}_{self.index}.log"
        self.start_time = None
        self.mc = None
        self.coll = None
        _log.thread_log_files[self.thread_name] = self.drivers_log_path

        try:
            mkdir(self.private_dir)
        except PermissionError:
            give_rwe_access(env.SLURMUSER, self.requester_home)
            mkdir(self.private_dir)

        mkdir(self.public_dir)
        mkdir(self.results_folder)
        mkdir(self.results_data_folder)
        mkdir(self.results_data_link)
        mkdir(self.patch_folder)

    def thread_log_setup(self):
        import threading
        from broker import config

        _log = logging.getLogger()  # root logger
        for hdlr in _log.handlers[:]:  # remove all old handlers
            _log.removeHandler(hdlr)

        #: dedicated per-thread handler
        thread_handler = logging.FileHandler(self.drivers_log_path, "a")
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        thread_handler.setFormatter(formatter)
        # The ThreadFilter makes sure this handler only accepts logrecords that originate
        # in *this* thread, only. It needs the current thread id for this:
        thread_handler.addFilter(ThreadFilter(thread_id=threading.get_ident()))
        config.logging.addHandler(thread_handler)
        time.sleep(0.25)
        # config.logging = logging
        # _log = logging.getLogger()
        # _log.addHandler(thread_handler)
        # config.logging = _log

    def check_already_cached(self, source_code_hash):
        if os.path.isfile(f"{self.private_dir}/{source_code_hash}.tar.gz"):
            log(f"==> {source_code_hash} is already cached in {self.private_dir}")
            self.is_already_cached[source_code_hash] = True
        elif os.path.isfile(f"{self.public_dir}/{source_code_hash}.tar.gz"):
            log(f"==> {source_code_hash} is already cached in {self.public_dir}")
            self.is_already_cached[source_code_hash] = True

    def complete_refund(self) -> str:
        """Complete refund back to the requester."""
        try:
            tx_hash = self.Ebb.refund(
                self.logged_job.args["provider"],
                env.PROVIDER_ID,
                self.job_key,
                self.index,
                self.job_id,
                self.cores,
                self.run_time,
            )
            log(f"==> refund() tx_hash={tx_hash}")
            return tx_hash
        except Exception as e:
            print_tb(e)
            raise e

    def is_md5sum_matches(self, path, name, _id, folder_type, cache_type) -> bool:
        output = generate_md5sum(path)
        if output == name:
            # checking is already downloaded folder's hash matches with the given hash
            if self.whoami() == "EudatClass" and folder_type != "":
                self.folder_type_dict[name] = folder_type

            self.cache_type[_id] = cache_type
            if cache_type == CacheType.PUBLIC:
                self.folder_path_to_download[name] = self.public_dir
                log(f"==> {name} is already cached under the public directory...", "blue")
            elif cache_type == CacheType.PRIVATE:
                self.folder_path_to_download[name] = self.private_dir
                log(f"==> {name} is already cached under the private directory")
            return True
        return False

    def is_cached(self, name, _id) -> bool:
        if self.cache_type[_id] == CacheType.PRIVATE:
            # Checks whether it is already exist under public cache directory
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
            # Checks whether it is already exist under the requesting user's private cache directory
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
                subprocess.check_output(
                    ["tar", "ztf", tar_path, "--wildcards", "*/run.sh"],
                    stderr=subprocess.DEVNULL,
                )
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

    def sbatch_call(self):
        try:
            link = Link(self.results_data_folder, self.results_data_link)
            link.link_folders()
            # file permission for the requester's foders should be reset
            give_rwe_access(self.requester_id, self.requester_home)
            give_rwe_access(env.WHOAMI, self.requester_home)
            self._sbatch_call()
        except Exception as e:
            print_tb(f"E: Failed to call _sbatch_call() function. {e}")
            raise e

    def _sbatch_call(self):
        job_key = self.logged_job.args["jobKey"]
        index = self.logged_job.args["index"]
        source_code_idx = 0  # 0 indicated maps to source_sode
        main_cloud_storage_id = self.logged_job.args["cloudStorageID"][source_code_idx]
        job_info = self.job_info[0]
        job_id = 0  # base job_id for them workflow
        job_block_number = self.logged_job.blockNumber
        date = (
            subprocess.check_output(  # cmd: date --date=1 seconds +%b %d %k:%M:%S %Y
                ["date", "--date=" + "1 seconds", "+%b %d %k:%M:%S %Y"],
                env={"LANG": "en_us_88591"},
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
        log(f"==> timestamp={timestamp}")
        write_to_file(f"{self.results_folder_prev}/timestamp.txt", timestamp)
        log(f"==> job_received_block_number={job_block_number}")
        logging.info("Adding recevied job into the mongoDB database.")
        # write_to_file(f"{results_folder_prev}/blockNumber.txt", job_block_number)
        self.Ebb.mongo_broker.add_item(
            job_key,
            self.index,
            self.source_code_hashes_str,
            self.requester_id,
            timestamp,
            main_cloud_storage_id,
            job_info,
        )

        # TODO: update as used_data_transfer_in value
        data_transfer_in_json = f"{self.results_folder_prev}/data_transfer_in.json"
        try:
            data = read_json(data_transfer_in_json)
        except:
            data = {}
            data["data_transfer_in"] = self.data_transfer_in_to_download_mb
            with open(data_transfer_in_json, "w") as outfile:
                json.dump(data, outfile)

            time.sleep(0.25)

        # seperator character is *
        run_file = f"{self.results_folder}/run.sh"
        sbatch_file_path = f"{self.results_folder}/{job_key}*{index}*{job_block_number}.sh"
        with open(f"{self.results_folder}/run_wrapper.sh", "w") as f:
            f.write("#!/bin/bash\n")
            f.write("#SBATCH -o slurm.out  # STDOUT\n")
            f.write("#SBATCH -e slurm.err  # STDERR\n")
            f.write("#SBATCH --mail-type=ALL\n")
            # _cmd = f"firejail --noprofile --net=none --disable-mnt --noblacklist={self.requester_home} bash {run_file}"
            _cmd = f"bash {run_file}"
            f.write(_cmd)

        # copyfile(f"{self.results_folder}/run.sh", sbatch_file_path)
        copyfile(f"{self.results_folder}/run_wrapper.sh", sbatch_file_path)
        job_core_num = str(job_info["core"][job_id])
        # client's requested seconds to run his/her job, 1 minute additional given
        execution_time_second = timedelta(seconds=int((job_info["run_time"][job_id] + 1) * 60))
        d = datetime(1, 1, 1) + execution_time_second
        time_limit = str(int(d.day) - 1) + "-" + str(d.hour) + ":" + str(d.minute)
        logging.info(f"time_limit={time_limit} | requested_core_num={job_core_num}")
        # give permission to user that will send jobs to Slurm.
        subprocess.check_output(["sudo", "chown", "-R", self.requester_id, self.results_folder])
        for _attempt in range(10):
            try:
                """Slurm submits job
                * Real mode -N is used. For Emulator-mode -N use 'sbatch -c'
                * cmd: sudo su - $requester_id -c "cd $results_folder && firejail --noprofile \
                        sbatch -c$job_core_num $results_folder/${job_key}*${index}.sh --mail-type=ALL
                """
                cmd = f'sbatch -N {job_core_num} "{sbatch_file_path}" --mail-type=ALL'
                with cd(self.results_folder):
                    try:
                        job_id = _run_as_sudo(env.SLURMUSER, cmd, shell=True)
                    except Exception as e:
                        if "Invalid account" in str(e):
                            remove_user(env.SLURMUSER)
                            add_user_to_slurm(env.SLURMUSER)
                            job_id = _run_as_sudo(env.SLURMUSER, cmd, shell=True)
                time.sleep(1)  # wait 1 second for slurm idle core to be updated
            except Exception as e:
                print_tb(e)
                slurm.remove_user(self.requester_id)
                slurm.add_user_to_slurm(self.requester_id)
            else:
                break
        else:
            sys.exit(1)

        try:
            slurm_job_id = job_id.split()[3]  # submitted batch job N
            log(f"==> slurm_job_id={slurm_job_id}")
            run(["scontrol", "update", f"jobid={slurm_job_id}", f"TimeLimit={time_limit}"])
        except Exception as e:
            print_tb(e)

        if not slurm_job_id.isdigit():
            logging.error("E: Detects an error on the SLURM side. slurm_job_id is not a digit")
            return False

        return True
