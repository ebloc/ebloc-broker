#!/usr/bin/env python3

import json
import networkx as nx
import os
import subprocess
import time
import uuid
from contextlib import suppress
from datetime import datetime, timedelta
from pathlib import Path
from shutil import copyfile
from typing import Dict, List

from broker import cfg
from broker._utils import _log
from broker._utils._log import ok
from broker._utils.tools import mkdir, read_json, squeue
from broker.config import ThreadFilter, env, logging
from broker.lib import calculate_size, log, run, subprocess_call
from broker.libs import slurm
from broker.libs.slurm import remove_user
from broker.libs.sudo import _run_as_sudo
from broker.libs.user_setup import add_user_to_slurm, give_rwe_access
from broker.link import Link
from broker.utils import (
    CacheID,
    bytes32_to_ipfs,
    cd,
    generate_md5sum,
    ipfs_to_bytes32,
    is_docker,
    is_ipfs_hash_valid,
    print_tb,
    write_to_file,
)
from broker.workflow.Workflow import Workflow


class BaseClass:
    def whoami(self):
        return type(self).__name__


class Storage(BaseClass):
    def __init__(self, **kwargs) -> None:
        self.Ebb = cfg.Ebb
        self.thread_name = uuid.uuid4().hex  # https://stackoverflow.com/a/44992275/2402577
        self.requester_id = kwargs.pop("requester_id")
        self.job_infos = kwargs.pop("job_infos")
        self.logged_job = kwargs.pop("logged_job")
        self.is_cached = kwargs.pop("is_cached")
        self.job_key = self.logged_job.args["jobKey"]
        self.index: int = self.logged_job.args["index"]
        self.cores = self.logged_job.args["core"]
        self.run_time: int = self.logged_job.args["runTime"]
        self.is_workflow: bool = False  # required during sbatch job submission
        self.job_id: int = 0
        self.cache_type = self.logged_job.args["cacheType"]
        self.data_transfer_in_requested = self.job_infos[0]["data_transfer_in"]
        self.data_transfer_in_to_download_mb = 0  # total size in MB to download
        self.code_hashes: List[bytes] = self.logged_job.args["sourceCodeHash"]
        self.code_hashes_str: List[str] = [bytes32_to_ipfs(_hash) for _hash in self.code_hashes]
        self.verified_data: Dict[str, bool] = {}
        self.registered_data_hashes: List[str] = []
        self.job_key_list: List[str] = []
        self.md5sum_dict: Dict[str, str] = {}
        self.folder_path_to_download: Dict[str, Path] = {}
        self.folder_type_dict: Dict[str, str] = {}
        self.PROGRAM_PATH = Path(env.PROGRAM_PATH)
        self.cloudStorageID = self.logged_job.args["cloudStorageID"]
        self.requester_home = self.PROGRAM_PATH / self.requester_id
        self.results_folder_prev = self.requester_home / f"{self.job_key}_{self.index}"
        self.results_folder = self.results_folder_prev / "JOB_TO_RUN"
        self.run_path = self.results_folder / "run.sh"
        self.results_data_folder = self.results_folder_prev / "data"
        self.results_data_link = self.results_folder_prev / "data_link"
        self.private_dir = self.requester_home / "cache"
        self.public_dir = self.PROGRAM_PATH / "cache"
        self.patch_dir = self.results_folder_prev / "patch"
        self.drivers_log_path = f"{env.LOG_DIR}/drivers_output/{self.job_key}_{self.index}.log"
        self.start_timestamp = None
        self.data_transfer_in_to_download: int = 0
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
        mkdir(self.patch_dir)

    def submit_slurm_job(self, job_core_num, sbatch_file_path):
        """Slurm submits job.

        - Real mode -n is used.
        - For Emulator-mode -N use `sbatch -c`
        - cmd:
        sudo su - $requester_id -c "cd $results_folder && firejail --noprofile \
            sbatch -c$job_core_num $results_folder/${job_key}*${index}.sh --mail-type=ALL

        sbatch -c1 *~*.sh
        """
        for _attempt in range(5):
            try:
                cmd = f'sbatch -n {job_core_num} "{sbatch_file_path}" --mail-type=ALL'
                if is_docker():  # user is already 'root'
                    # log(cmd, is_code=True)
                    output = run(["sbatch", "-n", f"{job_core_num}", f"{sbatch_file_path}"])
                    return output
                else:
                    with cd(self.results_folder):
                        try:
                            return _run_as_sudo(env.SLURMUSER, cmd, shell=True)
                        except Exception as e:
                            if "Invalid account" in str(e):
                                remove_user(env.SLURMUSER)
                                add_user_to_slurm(env.SLURMUSER)
                                job_id = _run_as_sudo(env.SLURMUSER, cmd, shell=True)

                time.sleep(2)  # wait 2 second for slurm idle core to be updated
            except Exception as e:
                print_tb(e)
                slurm.remove_user(self.requester_id)
                slurm.add_user_to_slurm(self.requester_id)

        raise Exception("sbatch could not submit the job")

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

    def check_already_cached(self, code_hash):
        if os.path.isfile(f"{self.private_dir}/{code_hash}.tar.gz"):
            log(f":beer:  [g]{code_hash}[/g] is already cached in {self.private_dir}")
            self.is_cached[code_hash] = True
        elif os.path.isfile(f"{self.public_dir}/{code_hash}.tar.gz"):
            log(f":beer:  [g]{code_hash}[/g] is already cached in {self.public_dir}")
            self.is_cached[code_hash] = True

    def full_refund(self) -> str:
        """Complete refund back to the requester."""
        try:
            log(f"warning: full refund is in process related to job_key={self.job_key}")
            tx_hash = self.Ebb.refund(
                self.logged_job.args["provider"],
                env.PROVIDER_ID,
                self.job_key,
                self.index,
                self.job_id,
                self.cores,
                self.run_time,
            )
            log(f"==> refund tx_hash={tx_hash}")
            return tx_hash
        except Exception as e:
            print_tb(e)

    def is_md5sum_matches(self, path, name, _id, folder_type, cache_type) -> bool:
        if generate_md5sum(path) == name:
            # checking is already downloaded folder's hash matches with the given hash
            if self.whoami() == "B2dropClass" and folder_type != "":
                self.folder_type_dict[name] = folder_type

            self.cache_type[_id] = cache_type
            if cache_type == CacheID.PUBLIC:
                self.folder_path_to_download[name] = self.public_dir
                log(f"==> {name} is already cached under the public directory", "blue")
            elif cache_type == CacheID.PRIVATE:
                self.folder_path_to_download[name] = self.private_dir
                log(f"==> {name} is already cached under the private directory")

            return True

        return False

    def _is_cached(self, name, _id) -> bool:
        if self.cache_type[_id] == CacheID.PRIVATE:
            #: checks whether it is already exist under public cache directory
            _cache_type = CacheID.PUBLIC
            cache_folder = f"{self.public_dir}/{name}"
            cached_tar_fn = f"{cache_folder}.tar.gz"
        else:
            #: checks whether it is already exist under the requesting user's private cache directory
            _cache_type = CacheID.PRIVATE
            cache_folder = self.private_dir
            cache_folder = f"{self.private_dir}/{name}"
            cached_tar_fn = f"{cache_folder}.tar.gz"

        if os.path.isfile(cached_tar_fn):
            if self.whoami() == "B2dropClass":
                self.folder_type_dict[name] = "tar.gz"

            return self.is_md5sum_matches(cached_tar_fn, name, _id, "", _cache_type)
        elif os.path.isfile(f"{cache_folder}/run.sh"):
            return self.is_md5sum_matches(cache_folder, name, _id, "folder", _cache_type)

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
                log(f"[m]./run.sh[/m] exists under the parent folder {ok()}")
                return True
            else:
                log("E: run.sh does not exist under the parent folder")
                return False
        except:
            log(f"E: run.sh file does not exist under the tar={tar_path}")
            return False

    def check_run_sh(self) -> bool:
        if not os.path.isfile(self.run_path):
            log(f"E: {self.run_path} file does not exist")
            return False

        return True

    def check_downloaded_folder_hash(self, fn, data_hash) -> bool:
        """Check hash of the downloaded file is correct or not."""
        if bool(generate_md5sum(fn) == data_hash):
            self.verified_data[data_hash] = True
            return True
        else:
            self.verified_data[data_hash] = False
            return False

    def submit_verified_data_files(self):
        verify_data_list = []
        for k, v in self.verified_data.items():
            if v:
                *_, output = self.Ebb.get_storage_info(k)
                received_block = output[0]
                is_verified_used = output[3]
                if received_block > 0 and not is_verified_used:
                    if len(k) == 32:
                        verify_data_list.append(k.encode("utf-8"))
                    elif is_ipfs_hash_valid(k):
                        verify_data_list.append(ipfs_to_bytes32(k))

        if verify_data_list:
            log("verify_data_list=", end="")
            log(verify_data_list)
            tx = cfg.Ebb.set_data_verified(verify_data_list)
            tx_hash = cfg.Ebb.tx_id(tx)
            log(f"verified_data_tx_hash={tx_hash}")

    def sbatch_call(self):
        try:
            link = Link(self.results_data_folder, self.results_data_link)
            if len(self.registered_data_hashes) > 0:
                # in case there there mounted folder first umount them in order
                # to give folder permission
                link.umount(self.registered_data_hashes)

            # folder permissions should be applied before linking the
            # folders in case there is a read-only folder. file permission for
            # the requester's foders should be reset
            give_rwe_access(self.requester_id, self.results_folder_prev)
            give_rwe_access(env.WHOAMI, self.results_folder_prev)
            # give_rwe_access(self.requester_id, self.requester_home)
            # give_rwe_access(env.WHOAMI, self.requester_home)
            if calculate_size(self.results_data_folder, _type="bytes") > 0:
                link.link_folders()

            if len(self.registered_data_hashes) > 0:
                link.registered_data(self.registered_data_hashes)

            self._sbatch_call()
            self.submit_verified_data_files()
        except Exception as e:
            print_tb(f"E: Failed to call _sbatch_call() function. {e}")
            raise e

    def scontrol_update(self, job_core_num, sbatch_file_path, time_limit):
        """Prevent scontrol update locked exception.

        scontrol generates: Job update not available right now, the DB index is being
        set, try again in a bit for job 5.
        """
        try:
            slurm_job_id = self.submit_slurm_job(job_core_num, sbatch_file_path)
            slurm_job_id = slurm_job_id.split()[3]
            cmd = ["scontrol", "update", f"jobid={slurm_job_id}", f"TimeLimit={time_limit}"]
            subprocess_call(cmd, attempt=10, sleep_time=10)
            return slurm_job_id
        except Exception as e:
            print_tb(e)
            raise e

    def run_wrapper(self, file_to_run, sbatch_file_path):
        with open(f"{self.results_folder}/run_wrapper.sh", "w") as f:
            f.write("#!/bin/bash\n")
            f.write("#SBATCH -o slurm.out  # STDOUT\n")
            f.write("#SBATCH -e slurm.err  # STDERR\n")
            f.write("#SBATCH --mail-type=ALL\n\n")
            if not is_docker():
                f.write(f"/usr/bin/unshare -r -n {file_to_run}")
            else:
                f.write(file_to_run)

        # print(sbatch_file_path)
        #: change file name based on the "job_key~index~job_bn~job_id"
        copyfile(f"{self.results_folder}/run_wrapper.sh", sbatch_file_path)
        # run(["chmod", "+x", sbatch_file_path])

    def _sbatch_call(self) -> bool:
        """Run sbatch on the cluster.

        * unshare: work fine for terminal programs.
        cmd: 'unshare -r -n ping google.com'

        __ https://askubuntu.com/a/600996/660555
        """
        job_key = self.logged_job.args["jobKey"]
        index = self.logged_job.args["index"]
        source_code_idx = 0  # 0 indicated maps to source_sode
        main_cloud_storage_id = self.logged_job.args["cloudStorageID"][source_code_idx]
        job_info = self.job_infos[0]
        dot_fn = self.results_folder / "sub_workflow_job.dot"
        if os.path.isfile(dot_fn):
            G = nx.drawing.nx_pydot.read_dot(dot_fn)
            if len(G.nodes) == 1:
                for node in list(G.nodes):
                    self.job_id = 0
                    break
        else:
            self.job_id = 0  # base job_id within the workflow

        job_bn = self.logged_job.blockNumber
        date = (
            subprocess.check_output(  # cmd: date --date=1 seconds +%b %d %k:%M:%S %Y
                ["date", "--date=" + "1 seconds", "+%b %d %k:%M:%S %Y"],
                env={"LANG": "en_us_88591"},
            )
            .decode("utf-8")
            .strip()
        )
        log(f" * {date} ", end="")
        write_to_file(self.results_folder_prev / "modified_date.txt", date)
        # cmd: echo date | date +%s
        p1 = subprocess.Popen(["echo", date], stdout=subprocess.PIPE)
        p2 = subprocess.Popen(["date", "+%s"], stdin=p1.stdout, stdout=subprocess.PIPE)
        p1.stdout.close()  # noqa
        timestamp = p2.communicate()[0].decode("utf-8").strip()
        log(f"timestamp={timestamp} | ", end="")
        write_to_file(self.results_folder_prev / "timestamp.txt", timestamp)
        log(f"job_received_bn={job_bn}")
        log("==> Adding recevied job into the mongoDB database")
        self.Ebb.mongo_broker.add_item(
            job_key,
            self.index,
            self.code_hashes_str,
            self.requester_id,
            timestamp,
            main_cloud_storage_id,
            job_info,
        )
        # TODO: update as used_data_transfer_in value
        data_transfer_in_json = self.results_folder_prev / "data_transfer_in.json"
        data = {}
        try:
            data = read_json(data_transfer_in_json)
        except:
            log(f"==> calculated_data_transfer_in={int(self.data_transfer_in_to_download_mb)} MB")
            data["data_transfer_in"] = int(self.data_transfer_in_to_download_mb)
            with open(data_transfer_in_json, "w") as outfile:
                json.dump(data, outfile)

            time.sleep(0.25)

        # if self.is_workflow:
        if os.path.isfile(self.results_folder / "sub_workflow_job.dot"):
            w = Workflow()
            if os.path.isfile(self.results_folder / "sub_workflow_job.dot"):
                dot_fn = self.results_folder / "sub_workflow_job.dot"
            else:
                dot_fn = self.results_folder / "workflow_job.dot"

            w.read_dot(dot_fn)
            time_limit_arr = []
            # for jobid in range(len(job_info["core"])):
            for jobid, node in enumerate(list(w.G_sorted())):
                if node != "\\n":
                    sbatch_file_path = self.results_folder / f"{job_key}~{index}~{job_bn}~{jobid}.sh"
                    file_to_run = f"{self.results_folder}/job{node}.sh"
                    self.run_wrapper(file_to_run, sbatch_file_path)
                    execution_time_second = timedelta(seconds=int((job_info["run_time"][jobid] + 1) * 60))
                    d = datetime(1, 1, 1) + execution_time_second
                    time_limit = str(int(d.day) - 1) + "-" + str(d.hour) + ":" + str(d.minute)
                    time_limit_arr.append(time_limit)
                    # log(f"==> time_limit={time_limit}")

            #: give permission to user that will send jobs to Slurm
            subprocess.check_output(["sudo", "chown", "-R", self.requester_id, self.results_folder])
            with cd(self.results_folder):
                w.sbatch_from_dot(
                    dot_fn,
                    f"{self.results_folder}/{job_key}",
                    index,
                    job_bn,
                    core_numbers=job_info["core"],
                    time_limits=time_limit_arr,
                )
        else:
            file_to_run = f"{self.results_folder}/run.sh"
            #: separator character is "~"
            if self.is_workflow:
                sbatch_file_path = self.results_folder / f"{job_key}~{index}~{job_bn}~{self.job_id}.sh"
            else:
                jobid = 0
                SINGLE = "3"
                sbatch_file_path = self.results_folder / f"{job_key}~{index}~{job_bn}~{self.job_id}~{SINGLE}.sh"

            self.run_wrapper(file_to_run, sbatch_file_path)
            job_core_num = str(job_info["core"][jobid])
            #: client's requested seconds to run his/her job, 1 minute additional given
            execution_time_second = timedelta(seconds=int((job_info["run_time"][jobid] + 1) * 60))
            d = datetime(1, 1, 1) + execution_time_second
            time_limit = str(int(d.day) - 1) + "-" + str(d.hour) + ":" + str(d.minute)
            log(f"==> time_limit=[cy]{time_limit}[/cy] | requested_core_num={job_core_num}")
            #: give permission to user that will send jobs to Slurm
            subprocess.check_output(["sudo", "chown", "-R", self.requester_id, self.results_folder])
            #: sbatch and update time limit
            slurm_job_id = self.scontrol_update(job_core_num, sbatch_file_path, time_limit)
            if not slurm_job_id.isdigit():
                log("E: Detect an error on the sbatch, slurm_job_id is not a digit")
                return False

        time.sleep(3)
        with suppress(Exception):
            job_ids = squeue()
            job_ids.remove("JOBID")

        log(f"==> ongoing_job_ids={job_ids}")
        return True
