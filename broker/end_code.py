#!/usr/bin/env python3

import base64
import getpass
import os
import pprint
import psutil
import shutil
import sys
import time
from contextlib import suppress
from pathlib import Path
from time import sleep
from typing import Dict, List

from broker import cfg
from broker._utils import _log
from broker._utils._log import WHERE, br, log, ok
from broker._utils.tools import _remove, exit_after, is_dir, mkdirs, pid_exists, read_json
from broker._utils.web3_tools import get_tx_status
from broker.config import env
from broker.errors import QuietExit
from broker.imports import connect
from broker.lib import (
    calculate_size,
    eblocbroker_function_call,
    remove_files,
    run,
    run_stdout_to_file,
    state,
    subprocess_call,
)
from broker.libs import _git, eudat, gdrive, slurm
from broker.utils import (
    StorageID,
    byte_to_mb,
    bytes32_to_ipfs,
    eth_address_to_md5,
    is_dir_empty,
    print_tb,
    read_file,
    remove_empty_files_and_folders,
)

ipfs = cfg.ipfs
Ebb = cfg.Ebb
connect()


class Common:
    """Prevent 'Class' to have attribute 'method' as mypy warnings."""

    def __init__(self) -> None:
        self.requester_home_path = Path("")
        self.results_folder: Path = Path("")
        self.results_folder_prev: Path = Path("")
        self.patch_file: Path = Path("")
        self.requester_gpg_fingerprint: str = ""
        self.patch_upload_fn = ""
        self.data_transfer_out: int = 0

    @exit_after(900)
    def _get_tx_status(self, tx_hash):
        get_tx_status(tx_hash)

    def initialize(self):
        pass


class Ipfs(Common):
    def upload(self, *_):
        """Upload nothing."""
        return


class IpfsGPG(Common):
    def upload(self, *_):
        """Upload patches right after all the patchings are completed."""
        try:
            from_gpg_fingerprint = ipfs.get_gpg_fingerprint(env.GMAIL).upper()
            ipfs.gpg_encrypt(from_gpg_fingerprint, self.requester_gpg_fingerprint, self.patch_file)
        except Exception as e:
            _remove(self.patch_file)
            raise e


class B2drop(Common):
    def __init__(self) -> None:
        self.encoded_share_tokens: Dict[str, str] = {}
        self.patch_dir: Path = Path("")

    def initialize(self):
        with suppress(Exception):
            eudat.login(env.OC_USER, env.LOG_DIR.joinpath(".b2drop_client.txt"), env.OC_CLIENT)

        try:
            self.get_shared_tokens()
        except Exception as e:
            print_tb(e)
            raise e

    def upload(self, code_hash, *_):
        with suppress(Exception):  # first time uploading
            uploaded_file_size = eudat.get_size(f_name=f"{code_hash}/{self.patch_upload_fn}")
            size_in_bytes = calculate_size(self.patch_file, _type="bytes")
            if uploaded_file_size == float(size_in_bytes):
                log(f"==> {self.patch_file} is already uploaded")
                return

        try:
            _data_transfer_out = calculate_size(self.patch_file)
            log(f"==> {br(code_hash)}.data_transfer_out={_data_transfer_out}MB")
            self.data_transfer_out += _data_transfer_out
            eudat.upload_results(
                self.encoded_share_tokens[code_hash], self.patch_upload_fn, self.patch_dir, max_retries=5
            )
        except Exception as e:
            raise e


class Gdrive(Common):
    def upload(self, key, is_job_key):
        """Upload the generated result into gdrive.

        :param key: key of the shared gdrive file
        :param is_job_key: is the provided key string is job's main key
        :returns: True if upload is successful
        """
        try:
            if not is_job_key:
                meta_data = gdrive.get_data_key_ids(self.results_folder_prev)
                key = meta_data[key]

            cmd = [env.GDRIVE, "info", "--bytes", key, "-c", env.GDRIVE_METADATA]
            gdrive_info = subprocess_call(cmd, 5, sleep_time=30)
        except Exception as e:
            raise Exception(f"{WHERE(1)} E: {key} does not have a match, meta_data={meta_data}. {e}") from e

        mime_type = gdrive.get_file_info(gdrive_info, "Mime")
        log(f"mime_type=[m]{mime_type}")
        self.data_transfer_out += calculate_size(self.patch_file)
        log(f"data_transfer_out={self.data_transfer_out} MB =>" f" rounded={int(self.data_transfer_out)} MB")
        if "folder" in mime_type:
            cmd = [env.GDRIVE, "upload", "--parent", key, self.patch_file, "-c", env.GDRIVE_METADATA]
        elif "gzip" in mime_type or "/zip" in mime_type:
            cmd = [env.GDRIVE, "update", key, self.patch_file, "-c", env.GDRIVE_METADATA]
        else:
            raise Exception("Files could not be uploaded")

        try:
            log(subprocess_call(cmd, 5))
        except Exception as e:
            print_tb(e)
            raise Exception("gdrive could not upload the file") from e


class ENDCODE(IpfsGPG, Ipfs, B2drop, Gdrive):
    def __init__(self, **kwargs) -> None:
        args = " ".join(["{!r}".format(v) for k, v in kwargs.items()])
        self.job_key: str = kwargs.pop("job_key")
        self.index = int(kwargs.pop("index"))
        self.received_bn: int = kwargs.pop("received_bn")
        self.folder_name: str = kwargs.pop("folder_name")
        self.slurm_job_id: int = kwargs.pop("slurm_job_id")
        self.share_tokens: Dict[str, str] = {}
        self.requester_id_address = ""
        self.data_transfer_in = 0
        self.data_transfer_out = 0
        self.elapsed_time = 0
        self.code_hashes_to_process: List[str] = []
        self.code_hashes: List[str] = []
        self.result_ipfs_hash: str = ""
        self.requester_gpg_fingerprint: str = ""
        self.end_timestamp = ""
        self.modified_date = None
        self.encoded_share_tokens: Dict[str, str] = {}
        #: set environment variables: https://stackoverflow.com/a/5971326/2402577
        os.environ["IPFS_PATH"] = str(env.HOME.joinpath(".ipfs"))
        _log.ll.LOG_FILENAME = Path(env.LOG_DIR) / "end_code_output" / f"{self.job_key}_{self.index}.log"
        self.job_id: int = 0  # TODO: should be mapped to slurm_job_id
        log(f"{env.EBLOCPATH}/broker/end_code.py {args}", "blue", is_code=True)
        log(f"==> slurm_job_id={self.slurm_job_id}")
        if self.job_key == self.index:
            log("E: given key and index are equal to each other")
            sys.exit(1)

        try:
            self.job_info = eblocbroker_function_call(
                lambda: Ebb.get_job_info(
                    env.PROVIDER_ID,
                    self.job_key,
                    self.index,
                    self.job_id,
                    self.received_bn,
                ),
                max_retries=10,
            )
            self.storage_ids = self.job_info["cloudStorageID"]
            requester_id = self.job_info["job_owner"]
            self.requester_id_address = eth_address_to_md5(requester_id)
            self.requester_info = Ebb.get_requester_info(requester_id)
        except Exception as e:
            log(f"E: {e}")
            sys.exit(1)

        self.requester_home_path = env.PROGRAM_PATH / self.requester_id_address
        self.results_folder_prev: Path = self.requester_home_path / f"{self.job_key}_{self.index}"
        self.results_folder = self.results_folder_prev / "JOB_TO_RUN"
        if not is_dir(self.results_folder) and not is_dir(self.results_folder_prev):
            sys.exit(1)

        self.results_data_link = Path(self.results_folder_prev) / "data_link"
        self.results_data_folder = Path(self.results_folder_prev) / "data"
        self.private_dir = Path(env.PROGRAM_PATH) / self.requester_id_address / "cache"
        self.patch_dir = Path(self.results_folder_prev) / "patch"
        self.patch_dir_ipfs = Path(self.results_folder_prev) / "patch_ipfs"
        mkdirs([self.patch_dir, self.patch_dir_ipfs])
        remove_empty_files_and_folders(self.results_folder)
        log(f" * whoami={getpass.getuser()} | id={os.getegid()}")
        log(f" * home={env.HOME}")
        log(f" * pwd={os.getcwd()}")
        log(f" * results_folder={self.results_folder}")
        log(f" * provider_id={env.PROVIDER_ID}")
        log(f" * job_key={self.job_key}")
        log(f" * index={self.index}")
        log(f" * storage_ids={self.storage_ids}")
        log(f" * folder_name=[white]{self.folder_name}")
        log(f" * requester_id_address={self.requester_id_address}")
        log(f" * received={self.job_info['received']}")
        self.job_state_running_pid = Ebb.mongo_broker.get_job_state_running_pid(self.job_key, self.index)
        with suppress(Exception):
            log(psutil.Process(int(self.job_state_running_pid)))
            while True:
                if not pid_exists(self.job_state_running_pid):
                    break
                else:
                    log("#> job_state_running() is still running; sleeping for 15 seconds")
                    sleep(15)

        self.job_state_running_tx = Ebb.mongo_broker.get_job_state_running_tx(self.job_key, self.index)
        log(f"==> job_state_running_tx={self.job_state_running_tx}")

    def get_shared_tokens(self):
        with suppress(Exception):
            share_ids = read_json(f"{self.private_dir}/{self.job_key}_share_id.json")

        for code_hash in self.code_hashes_to_process:
            try:
                share_token = share_ids[code_hash]["share_token"]
                self.share_tokens[code_hash] = share_token
                self.encoded_share_tokens[code_hash] = base64.b64encode((f"{share_token}:").encode("utf-8")).decode(
                    "utf-8"
                )
            except KeyError:
                try:
                    shared_id = Ebb.mongo_broker.find_shareid_item(f"{self.job_key}_{self.requester_id_address[:16]}")
                    share_token = shared_id["share_token"]
                    self.share_tokens[code_hash] = share_token
                    self.encoded_share_tokens[code_hash] = base64.b64encode((f"{share_token}:").encode("utf-8")).decode(
                        "utf-8"
                    )
                except Exception as e:
                    log(f"E: share_id cannot be detected from key={self.job_key}")
                    raise e

        for key in share_ids:
            value = share_ids[key]
            try:
                encoded_value = self.encoded_share_tokens[key]
            except:
                _share_token = share_ids[key]["share_token"]
                encoded_value = base64.b64encode((f"{_share_token}:").encode("utf-8")).decode("utf-8")

            log(f"## shared_tokens: {key} => {value['share_token']} | encoded={encoded_value}")

    def get_cloud_storage_class(self, _id):
        """Return cloud storage used for the id of the data."""
        if self.storage_ids[_id] == StorageID.IPFS:
            return Ipfs
        if self.storage_ids[_id] == StorageID.IPFS_GPG:
            return IpfsGPG
        if self.storage_ids[_id] == StorageID.B2DROP:
            return B2drop
        if self.storage_ids[_id] == StorageID.GDRIVE:
            return Gdrive

        raise Exception(f"corresponding storage_id_class={self.storage_ids[_id]} does not exist")

    def set_code_hashes_to_process(self):
        for idx, code_hash in enumerate(self.code_hashes):
            if self.storage_ids[idx] in [StorageID.IPFS, StorageID.IPFS_GPG]:
                ipfs_hash = bytes32_to_ipfs(code_hash)
                self.code_hashes_to_process.append(ipfs_hash)
            else:
                self.code_hashes_to_process.append(cfg.w3.toText(code_hash))

    def _ipfs_add_folder(self, folder_path):
        try:
            self.result_ipfs_hash = ipfs.add(folder_path)
            log(f"==> result_ipfs_hash={self.result_ipfs_hash}")
            ipfs.pin(self.result_ipfs_hash)
            data_transfer_out = ipfs.get_cumulative_size(self.result_ipfs_hash)
        except Exception as e:
            print_tb(e)
            raise e

        data_transfer_out = byte_to_mb(data_transfer_out)
        self.data_transfer_out += data_transfer_out

    def process_payment_tx(self):
        try:
            tx_hash = Ebb.process_payment(
                self.job_key,
                self.index,
                self.job_id,
                self.elapsed_time,
                self.result_ipfs_hash,
                self.storage_ids,
                self.end_timestamp,
                self.data_transfer_in,
                self.data_transfer_out,
                self.job_info["core"],
                self.job_info["run_time"],
                self.received_bn,
            )
        except Exception as e:
            print_tb(e)
            sys.exit(1)

        log(f"==> [white]process_payment {self.job_key} {self.index}")
        return tx_hash

    def clean_before_upload(self) -> None:
        remove_files(f"{self.results_folder}/.node-xmlhttprequest*")

    def remove_source_code(self) -> None:
        """Client's initial downloaded files are removed."""
        timestamp_fn = f"{self.results_folder_prev}/timestamp.txt"
        try:
            cmd = ["find", self.results_folder, "-type", "f", "!", "-newer", timestamp_fn]
            files_to_remove = run(cmd)
            if files_to_remove:
                log(f"## Files to be removed: \n{files_to_remove}\n")
        except Exception as e:
            print_tb(e)
            sys.exit()

        run(["find", self.results_folder, "-type", "f", "!", "-newer", timestamp_fn, "-delete"])

    def git_diff_patch_and_upload(self, source_fn: Path, name, storage_class, is_job_key) -> None:
        if is_job_key:
            log(f"==> base_patch={self.patch_dir}")
            log(f"==> source_code_patch={name}")
        else:
            log(f"==> data_file_patch={name}")

        try:
            if storage_class is Ipfs or storage_class is IpfsGPG:
                target_path = self.patch_dir_ipfs
            else:
                target_path = self.patch_dir

            self.patch_upload_fn, self.patch_file, is_file_empty = _git.diff_patch(
                source_fn, name, self.index, target_path, self.requester_home_path
            )
            if not is_file_empty:
                try:
                    storage_class.upload(self, name, is_job_key)
                except Exception as e:
                    print_tb(e)
                    raise e
        except Exception as e:
            print_tb(e)
            raise Exception("problem on the git_diff_patch_and_upload() function") from e

    def upload_driver(self):
        self.clean_before_upload()
        try:
            storage_class = self.get_cloud_storage_class(0)
            self.git_diff_patch_and_upload(self.results_folder, self.job_key, storage_class, is_job_key=True)
        except Exception as e:
            raise e

        for idx, name in enumerate(self.code_hashes_to_process[1:], 1):
            # starting from 1st index for data files
            try:
                if not self.storage_ids[idx] == StorageID.NONE:
                    storage_class = self.get_cloud_storage_class(idx)
                    self.git_diff_patch_and_upload(
                        self.results_data_folder / name, name, storage_class, is_job_key=False
                    )
                else:
                    pass
            except Exception as e:
                print_tb(e)
                raise e

        if not is_dir_empty(self.patch_dir_ipfs):
            # it will upload files after all the patchings are completed
            # in case any file is created via ipfs
            self._ipfs_add_folder(self.patch_dir_ipfs)

    def sacct_result(self):
        """Return sacct output for the job.

        CPUTime = NCPUS * Elapsed

        To get stats about real CPU usage you need to look at SystemCPU and
        UserCPU, but the docs warns that it only measure CPU time for the parent
        process and not for child processes.
        """
        slurm_log_output_fn = f"{self.results_folder}/slurm_job_info.out"
        slurm_log_output_fn_temp = f"{self.results_folder}/slurm_job_info.out~"
        cmd = ["sacct", "-X", "--job", self.slurm_job_id, "--format"]
        cmd.append("jobID,jobname,user,account,group,cluster,allocCPUS,REQMEM,TotalCPU,elapsed")
        run_stdout_to_file(cmd, slurm_log_output_fn)
        with open(slurm_log_output_fn, "a") as f:
            f.write("\n\n")

        cmd.pop()
        cmd.append("NNodes,NTasks,ncpus,CPUTime,State,ExitCode,End,CPUTime,MaxRSS")
        run_stdout_to_file(cmd, slurm_log_output_fn, mode="a")
        with open(slurm_log_output_fn, "a") as f:
            f.write("\n")

        shutil.move(slurm_log_output_fn, slurm_log_output_fn_temp)
        open(slurm_log_output_fn, "w").close()
        with open(slurm_log_output_fn_temp) as f1, open(slurm_log_output_fn, "w") as f2:
            line = f1.read().strip()
            if "--" in line:
                line = line.replace("-", "=")

            f2.write(line)

        os.remove(slurm_log_output_fn_temp)

    def get_job_info(self, is_print=False, is_log_print=True) -> None:
        self.job_info = eblocbroker_function_call(
            lambda: Ebb.get_job_info(
                env.PROVIDER_ID,
                self.job_key,
                self.index,
                self.job_id,
                self.received_bn,
                is_print=is_print,
                is_log_print=is_log_print,
            ),
            max_retries=1,
        )

    def attemp_get_job_info(self):
        is_print = True
        sleep_time = 30
        for attempt in range(10):
            # log(self.job_info)
            if self.job_info["stateCode"] == state.code["RUNNING"]:
                # it will come here eventually, when setJob() is deployed. Wait
                # until does values updated on the blockchain
                log("## job has been started")
                return

            if self.job_info["stateCode"] == state.code["COMPLETED"]:
                # detects an error on the slurm side
                log("warning: job is already completed and its money is received")
                self.get_job_info()
                raise QuietExit

            try:
                self.job_info = Ebb.get_job_info(
                    env.PROVIDER_ID, self.job_key, self.index, self.job_id, self.received_bn, is_print
                )
                is_print = False
            except Exception as e:
                print_tb(e)
                # sys.exit(1)

            # sleep here so this loop is not keeping CPU busy due to
            # start_code tx may deploy late into the blockchain.
            log(
                f"==> {br(attempt)} start_code tx of the job is not obtained yet, "
                f"waiting for {sleep_time} seconds to pass...",
                end="",
            )
            sleep(sleep_time)
            log(ok())

        log("E: failed all the attempts, abort")
        sys.exit(1)

    def remove_job_folder(self):
        """Remove downloaded code from local since it is not needed anymore; garbage collector."""
        _remove(self.results_folder)

    def run(self):
        try:
            data = read_json(f"{self.results_folder_prev}/data_transfer_in.json")
            self.data_transfer_in = data["data_transfer_in"]
            log(f"==> data_transfer_in={self.data_transfer_in} MB -> rounded={int(self.data_transfer_in)} MB")
        except:
            log("E: data_transfer_in.json file does not exist")

        try:
            self.modified_date = read_file(f"{self.results_folder_prev}/modified_date.txt")
            log(f"==> modified_date={self.modified_date}")
        except:
            log("E: modified_date.txt file could not be read")

        self.requester_gpg_fingerprint = self.requester_info["gpg_fingerprint"]
        log("\njob owner's info\n================", "green")
        log(f"==> gmail=[white]{self.requester_info['gmail']}")
        log(f"==> gpg_fingerprint={self.requester_gpg_fingerprint}")
        log(f"==> ipfs_address={self.requester_info['ipfs_address']}")
        log(f"==> f_id={self.requester_info['f_id']}")
        if self.job_info["stateCode"] == str(state.code["COMPLETED"]):
            self.get_job_info()
            log(":beer: job is already completed and its money is received", "green")
            raise QuietExit

        run_time = self.job_info["run_time"]
        log(f"==> requested_run_time={run_time[self.job_id]} minutes")
        try:
            if self.job_state_running_tx:
                Ebb._wait_for_transaction_receipt(self.job_state_running_tx)
            else:
                log("warning: job_state_running_tx is empty")

            self.get_job_info(is_log_print=False)  # re-fetch job info
            self.attemp_get_job_info()
        except Exception as e:
            print_tb(e)
            raise e

        log(f"## receive state of the running job  {ok()}")
        try:
            self.job_info = eblocbroker_function_call(
                lambda: Ebb.get_job_code_hashes(
                    env.PROVIDER_ID,
                    self.job_key,
                    self.index,
                    # self.job_id,
                    self.received_bn,
                ),
                max_retries=10,
            )
        except Exception as e:
            print_tb(e)
            sys.exit(1)

        self.code_hashes = self.job_info["code_hashes"]
        self.set_code_hashes_to_process()
        self.sacct_result()
        self.end_timestamp = slurm.get_job_end_timestamp(self.slurm_job_id)
        self.elapsed_time = slurm.get_elapsed_time(self.slurm_job_id)
        if self.elapsed_time > int(run_time[self.job_id]):
            self.elapsed_time = run_time[self.job_id]

        log(f"finalized_elapsed_time={self.elapsed_time}")
        log("job_info=", end="")
        log(pprint.pformat(self.job_info))
        try:
            self.get_cloud_storage_class(0).initialize(self)
            self.upload_driver()
        except Exception as e:
            print_tb(e)
            sys.exit(1)

        data_transfer_sum = self.data_transfer_in + self.data_transfer_out
        log(f"==> data_transfer_in={self.data_transfer_in} MB -> rounded={int(self.data_transfer_in)} MB")
        log(f"==> data_transfer_out={self.data_transfer_out} MB -> rounded={int(self.data_transfer_out)} MB")
        log(f"==> data_transfer_sum={data_transfer_sum} MB -> rounded={int(data_transfer_sum)} MB")
        tx_hash = self.process_payment_tx()
        time.sleep(1)
        self._get_tx_status(tx_hash)
        self.get_job_info()
        log("SUCCESS")
        # self.remove_job_folder()  # FIXME: TESTING


if __name__ == "__main__":
    kwargs = {
        "job_key": sys.argv[1],
        "index": sys.argv[2],
        "received_bn": sys.argv[3],
        "folder_name": sys.argv[4],
        "slurm_job_id": sys.argv[5],
    }
    try:
        cloud_storage = ENDCODE(**kwargs)
        cloud_storage.run()
    except QuietExit:
        pass
    except Exception as e:
        print_tb(e)
