#!/usr/bin/env python3

import base64
import getpass
import os
import pprint
import sys
import time
from typing import Dict, List

import eblocbroker.Contract as Contract
import libs.eudat as eudat
import libs.gdrive as gdrive
import libs.git as git
import libs.ipfs as ipfs
import libs.slurm as slurm

from broker.config import QuietExit, env, logging, setup_logger
from broker.imports import connect
from broker.lib import (
    calculate_folder_size,
    eblocbroker_function_call,
    is_dir,
    remove_files,
    run,
    run_stdout_to_file,
    state,
    subprocess_call,
)
from broker.utils import (
    WHERE,
    StorageID,
    _colorize_traceback,
    byte_to_mb,
    bytes32_to_ipfs,
    eth_address_to_md5,
    is_dir_empty,
    log,
    mkdir,
    read_file,
    read_json,
    remove_empty_files_and_folders,
    silent_remove,
)

eBlocBroker, w3 = connect()
Ebb = Contract.eblocbroker = Contract.Contract()


class Common:
    """Prevents "Class" has no attribute "method" mypy warnings."""

    def __init__(self) -> None:
        self.results_folder = ""
        self.results_folder_prev = ""
        self.patch_file = ""
        self.requester_gpg_fingerprint = ""
        self.patch_upload_name = ""
        self.data_transfer_out = 0.0


class IpfsGPG(Common):
    def initialize(self):  # noqa
        pass

    def upload(self, *_) -> bool:
        """Upload files right after all the patchings are completed."""
        try:
            ipfs.gpg_encrypt(self.requester_gpg_fingerprint, self.patch_file)
        except:
            silent_remove(self.patch_file)
            sys.exit(1)
        return True


class Ipfs(Common):
    def initialize(self):  # noqa
        pass

    def upload(self, *_) -> bool:
        """Upload files after all the patchings are completed."""
        return True


class Eudat(Common):
    def __init__(self) -> None:
        self.encoded_share_tokens = {}  # type: Dict[str, str]

    def initialize(self):
        try:
            eudat.login(env.OC_USER, f"{env.LOG_PATH}/.eudat_provider.txt", env.OC_CLIENT)
        except:
            pass

        try:
            self.get_shared_tokens()
        except:
            sys.exit(1)

    def upload(self, source_code_hash, *_) -> bool:
        try:
            uploaded_file_size = eudat.get_size(f_name=f"{source_code_hash}/{self.patch_upload_name}")
            size_in_bytes = calculate_folder_size(self.patch_file, _type="bytes")
            if uploaded_file_size == float(size_in_bytes):
                log(f"==> {self.patch_file} is already uploaded")
                return True
        except Exception:  # First time uploading
            pass

        _data_transfer_out = calculate_folder_size(self.patch_file)
        logging.info(f"[{source_code_hash}]'s data_transfer_out => {_data_transfer_out} MB")
        self.data_transfer_out += _data_transfer_out
        success = eudat.upload_results(
            self.encoded_share_tokens[source_code_hash],
            self.patch_upload_name,
            self.patch_folder,
            5,
        )
        return success


class Gdrive(Common):
    def initialize(self):
        pass

    def upload(self, key, is_job_key) -> bool:
        try:
            if not is_job_key:
                success, meta_data = gdrive.get_data_key_ids(self.results_folder_prev)
                if not success:
                    return False

                try:
                    key = meta_data[key]
                except:
                    logging.error(f"[{WHERE(1)}] E: {key} does not have a match in meta_data.json")
                    return False

            cmd = [env.GDRIVE, "info", "--bytes", key, "-c", env.GDRIVE_METADATA]
            gdrive_info = subprocess_call(cmd, 5)
        except:
            logging.error(f"[{WHERE(1)}] E: {key} does not have a match. meta_data={meta_data}")
            return False

        mime_type = gdrive.get_file_info(gdrive_info, "Mime")
        logging.info(f"mime_type={mime_type}")
        self.data_transfer_out += calculate_folder_size(self.patch_file)
        logging.info(f"data_transfer_out={self.data_transfer_out} MB => rounded={int(self.data_transfer_out)} MB")
        if "folder" in mime_type:
            cmd = [env.GDRIVE, "upload", "--parent", key, self.patch_file, "-c", env.GDRIVE_METADATA]
        elif "gzip" in mime_type or "/zip" in mime_type:
            cmd = [env.GDRIVE, "update", key, self.patch_file, "-c", env.GDRIVE_METADATA]
        else:
            logging.error("E: Files could not be uploaded")
            return False

        try:
            logging.info(subprocess_call(cmd, 5))
        except:
            logging.error(f"[{WHERE(1)}] E: gdrive could not upload the file")
            return False

        return True


class ENDCODE(IpfsGPG, Ipfs, Eudat, Gdrive):
    def __init__(self, **kwargs) -> None:
        args = " ".join(["{!r}".format(v) for k, v in kwargs.items()])
        self.job_key = kwargs.pop("job_key")
        self.index = kwargs.pop("index")
        self.received_block_number = kwargs.pop("received_block_number")
        self.folder_name = kwargs.pop("folder_name")
        self.slurm_job_id = kwargs.pop("slurm_job_id")
        self.share_tokens = {}  # type: Dict[str, str]
        self.data_transfer_in = 0
        self.data_transfer_out = 0.0
        self.elapsed_time = 0
        self.source_code_hashes_to_process: List[str] = []
        self.source_code_hashes: List[str] = []
        self.result_ipfs_hash = ""
        self.requester_gpg_fingerprint = ""
        self.end_time_stamp = ""
        self.modified_date = None
        self.encoded_share_tokens = {}  # type: Dict[str, str]

        # [https://stackoverflow.com/a/4453495/2402577, https://stackoverflow.com/a/5971326/2402577]
        # my_env = os.environ.copy();
        # my_env["IPFS_PATH"] = HOME + "/.ipfs"
        # print(my_env)
        os.environ["IPFS_PATH"] = f"{env.HOME}/.ipfs"
        logging = setup_logger(f"{env.LOG_PATH}/end_code_output/{self.job_key}_{self.index}.log")
        # logging.info(f"==> Entered into {self.__class__.__name__} case.") # delete
        # logging.info(f"START: {datetime.datetime.now()}") # delete
        self.job_id = 0  # TODO: should be mapped slurm_job_id
        log(f"{env.EBLOCPATH}/broker/end_code.py {args}", "blue")
        log(f"slurm_job_id={self.slurm_job_id}")
        if self.job_key == self.index:
            logging.error("E: Given key and index are equal to each other")
            sys.exit(1)

        try:
            self.job_info = eblocbroker_function_call(
                lambda: Ebb.get_job_info(
                    env.PROVIDER_ID,
                    self.job_key,
                    self.index,
                    self.job_id,
                    self.received_block_number,
                ),
                10,
            )
            self.cloud_storage_ids = self.job_info["cloudStorageID"]
            requester_id = self.job_info["job_owner"]
            requester_id_address = eth_address_to_md5(requester_id)
            self.requester_info = Ebb.get_requester_info(requester_id)
        except:
            sys.exit(1)

        self.results_folder_prev = f"{env.PROGRAM_PATH}/{requester_id_address}/{self.job_key}_{self.index}"
        self.results_folder = f"{self.results_folder_prev}/JOB_TO_RUN"
        if not is_dir(self.results_folder) and not is_dir(self.results_folder_prev):
            sys.exit(1)

        self.results_data_link = f"{self.results_folder_prev}/data_link"
        self.results_data_folder = f"{self.results_folder_prev}/data"
        self.private_dir = f"{env.PROGRAM_PATH}/{requester_id_address}/cache"
        self.patch_folder = f"{self.results_folder_prev}/patch"
        self.patch_folder_ipfs = f"{self.results_folder_prev}/patch_ipfs"

        mkdir(self.patch_folder)
        mkdir(self.patch_folder_ipfs)

        remove_empty_files_and_folders(self.results_folder)
        log(f"whoami: {getpass.getuser()} - {os.getegid()}")
        log(f"home: {env.HOME}")
        log(f"pwd: {os.getcwd()}")
        log(f"results_folder: {self.results_folder}")
        log(f"job_key: {self.job_key}")
        log(f"index: {self.index}")
        log(f"cloud_storage_ids: {self.cloud_storage_ids}")
        log(f"folder_name: {self.folder_name}")
        log(f"provider_id: {env.PROVIDER_ID}")
        log(f"requester_id_address: {requester_id_address}")
        log(f"received: {self.job_info['received']}")

    def get_shared_tokens(self):
        try:
            share_ids = read_json(f"{self.private_dir}/{self.job_key}_shareID.json")
        except:
            pass

        for source_code_hash in self.source_code_hashes_to_process:
            try:
                share_token = share_ids[source_code_hash]["share_token"]
                self.share_tokens[source_code_hash] = share_token
                self.encoded_share_tokens[source_code_hash] = base64.b64encode(
                    (f"{share_token}:").encode("utf-8")
                ).decode("utf-8")
            except KeyError:
                try:
                    share_token = Ebb.mongo_broker.find_key(Ebb.mongo_broker.mc["eBlocBroker"]["shareID"], self.job_key)
                    self.share_tokens[source_code_hash] = share_token
                    self.encoded_share_tokens[source_code_hash] = base64.b64encode(
                        (f"{share_token}:").encode("utf-8")
                    ).decode("utf-8")
                except:
                    logging.error(f"E: share_id cannot detected from key: {self.job_key}")
                    raise

        for key in share_ids:
            value = share_ids[key]
            encoded_value = self.encoded_share_tokens[key]
            logging.info("shared_tokens: ({}) => ({}) encoded:({})".format(key, value["share_token"], encoded_value))

    def get_cloud_storage_class(self, _id):
        """Returns cloud storage used for the id of the data."""
        if self.cloud_storage_ids[_id] == StorageID.IPFS:
            return Ipfs
        if self.cloud_storage_ids[_id] == StorageID.IPFS_GPG:
            return IpfsGPG
        if self.cloud_storage_ids[_id] == StorageID.EUDAT:
            return Eudat
        if self.cloud_storage_ids[_id] == StorageID.GDRIVE:
            return Gdrive
        return None

    def set_source_code_hashes_to_process(self):
        for idx, source_code_hash in enumerate(self.source_code_hashes):
            if self.cloud_storage_ids[idx] in [StorageID.IPFS, StorageID.IPFS_GPG]:
                ipfs_hash = bytes32_to_ipfs(source_code_hash)
                self.source_code_hashes_to_process.append(ipfs_hash)
            else:
                self.source_code_hashes_to_process.append(w3.toText(source_code_hash))

    def ipfs_add_folder(self, folder_path):
        try:
            self.result_ipfs_hash = ipfs.add(folder_path)
            logging.info(f"result_ipfs_hash={self.result_ipfs_hash}")
            ipfs.pin(self.result_ipfs_hash)
            data_transfer_out = ipfs.get_cumulative_size(self.result_ipfs_hash)
        except:
            _colorize_traceback()
            raise

        data_transfer_out = byte_to_mb(data_transfer_out)
        self.data_transfer_out += data_transfer_out

    def process_payment_tx(self):
        try:
            tx_hash = eblocbroker_function_call(
                lambda: Ebb.process_payment(
                    self.job_key,
                    self.index,
                    self.job_id,
                    self.elapsed_time,
                    self.result_ipfs_hash,
                    self.cloud_storage_ids,
                    self.end_time_stamp,
                    self.data_transfer_in,
                    self.data_transfer_out,
                    self.job_info["core"],
                    self.job_info["run_time"],
                ),
                10,
            )
            logging.info(f"tx_hash={tx_hash}")
        except:
            _colorize_traceback()
            sys.exit(1)

        with open(f"{env.LOG_PATH}/transactions/{env.PROVIDER_ID}.txt", "a") as f:
            f.write(f"processPayment {self.job_key} {self.index} {tx_hash}")

    def clean_before_upload(self):
        remove_files(f"{self.results_folder}/.node-xmlhttprequest*")

    def remove_source_code(self):
        """Client's initial downloaded files are removed."""
        timestamp_file = f"{self.results_folder_prev}/timestamp.txt"
        try:
            cmd = ["find", self.results_folder, "-type", "f", "!", "-newer", timestamp_file]
            files_to_remove = run(cmd)
        except Exception as e:
            _colorize_traceback(e)
            sys.exit()

        if not files_to_remove or files_to_remove:
            logging.info(f"Files to be removed: \n{files_to_remove}\n")

        run(["find", self.results_folder, "-type", "f", "!", "-newer", timestamp_file, "-delete"])

    def git_diff_patch_and_upload(self, source, name, storage_class, is_job_key):
        if is_job_key:
            log(f"==> patch_base={self.patch_folder}")
            log(f"==> Patch for the source code {name}")
        else:
            log(f"==> Patch for the data file {name}")

        try:
            if storage_class is Ipfs or storage_class is IpfsGPG:
                target_path = self.patch_folder_ipfs
            else:
                target_path = self.patch_folder

            self.patch_upload_name, self.patch_file, is_file_empty = git.diff_patch(
                source, name, self.index, target_path
            )
            if not is_file_empty:
                if not storage_class.upload(self, name, is_job_key):
                    raise
        except Exception as e:
            raise Exception("E: Problem on git_diff_patch_and_upload()") from e

    def upload_driver(self):
        self.clean_before_upload()
        try:
            storage_class = self.get_cloud_storage_class(0)
            self.git_diff_patch_and_upload(self.results_folder, self.job_key, storage_class, is_job_key=True)
        except Exception as e:
            raise Exception("E: Problem on git_diff_patch_and_upload()") from e

        for idx, name in enumerate(self.source_code_hashes_to_process[1:], 1):
            # starting from 1st index for data files
            source = f"{self.results_data_folder}/{name}"
            storage_class = self.get_cloud_storage_class(idx)
            try:
                self.git_diff_patch_and_upload(source, name, storage_class, is_job_key=False)
            except Exception as e:
                raise Exception("E: Problem on git_diff_patch_and_upload()") from e

        if not is_dir_empty(self.patch_folder_ipfs):
            # it will upload files after all the patchings are completed
            # in case any file is created via ipfs
            self.ipfs_add_folder(self.patch_folder_ipfs)

    def sacct_result(self):
        # CPUTime = NCPUS * Elapsed
        #
        # To get stats about real CPU usage you need to look at SystemCPU and
        # UserCPU, but the docs warns that it only measure CPU time for the
        # parent process and not for child processes.
        slurm_log_output_file = f"{self.results_folder}/slurm_job_info.out"
        cmd = ["sacct", "-X", "--job", self.slurm_job_id, "--format"]
        cmd.append("JobID,jobname,User,Account,Group,Cluster,AllocCPUS,REQMEM,TotalCPU,Elapsed")
        run_stdout_to_file(cmd, slurm_log_output_file)
        with open(slurm_log_output_file, "a") as myfile:
            myfile.write("\n\n")

        cmd.pop()
        cmd.append("NNodes,NTasks,ncpus,CPUTime,State,ExitCode,End,CPUTime,MaxRSS")
        run_stdout_to_file(cmd, slurm_log_output_file, mode="a")
        with open(slurm_log_output_file, "a") as myfile:
            myfile.write("\n")

    def run(self):
        try:
            data = read_json(f"{self.results_folder_prev}/data_transfer_in.json")
            self.data_transfer_in = data["data_transfer_in"]
            log(f"==> data_transfer_in={self.data_transfer_in} MB -> rounded={int(self.data_transfer_in)} MB")
        except:
            logging.error("E: data_transfer_in.json does not exist")

        try:
            self.modified_date = read_file(f"{self.results_folder_prev}/modified_date.txt")
            log(f"==> modified_date={self.modified_date}")
        except:
            log("E: modified_date.txt file could not be read")

        self.requester_gpg_fingerprint = self.requester_info["gpg_fingerprint"]
        log("job_owner's info", "green")
        log("================", "green")
        log("{0: <17}".format("email:") + self.requester_info["email"], "green")
        log("{0: <17}".format("gpg_fingerprint:") + self.requester_gpg_fingerprint, "green")
        log("{0: <17}".format("ipfs_id:") + self.requester_info["ipfs_id"], "green")
        log("{0: <17}".format("f_id:") + self.requester_info["f_id"], "green")

        if self.job_info["stateCode"] == str(state.code["COMPLETED"]):
            log("==> Job is already completed and its money is received")
            raise QuietExit

        run_time = self.job_info["run_time"]
        log(f"==> requested_run_time={run_time[self.job_id]} minutes")
        is_print = True
        for attempt in range(10):
            if self.job_info["stateCode"] == state.code["RUNNING"]:
                # it will come here eventually, when setJob() is deployed
                log("==> Job has been started")
                break  # wait until does values updated on the blockchain

            if self.job_info["stateCode"] == state.code["COMPLETED"]:
                # detects an error on the slurm side
                log("==> Job is already completed job and its money is received")
                raise QuietExit

            try:
                self.job_info = eblocbroker_function_call(
                    lambda: Ebb.get_job_info(
                        env.PROVIDER_ID, self.job_key, self.index, self.job_id, self.received_block_number, is_print
                    ),
                    10,
                )
                is_print = False
            except:
                sys.exit(1)

            log(f"==> start_code tx of the job is not obtained yet.\nWaiting for {attempt * 15} seconds to pass")
            # short sleep here so this loop is not keeping CPU busy due to
            # setJobSuccess may deploy late
            time.sleep(15)
        else:  # failed all the attempts, abort
            sys.exit(1)

        try:
            self.job_info = eblocbroker_function_call(
                lambda: Ebb.get_job_source_code_hashes(
                    self.job_info,
                    env.PROVIDER_ID,
                    self.job_key,
                    self.index,
                    self.job_id,
                    self.received_block_number,
                ),
                10,
            )
        except:
            sys.exit(1)

        self.source_code_hashes = self.job_info["source_code_hash"]
        self.set_source_code_hashes_to_process()
        self.sacct_result()

        self.end_time_stamp = slurm.get_job_end_time(self.slurm_job_id)
        self.elapsed_time = slurm.get_elapsed_time(self.slurm_job_id)
        if self.elapsed_time > int(run_time[self.job_id]):
            self.elapsed_time = run_time[self.job_id]

        logging.info(f"finalized_elapsed_time={self.elapsed_time}")
        _job_info = pprint.pformat(self.job_info)
        log(f"## job_info:\n{_job_info}", "green")
        try:
            self.get_cloud_storage_class(0).initialize(self)
            self.upload_driver()
        except:
            _colorize_traceback()
            sys.exit(1)

        data_transfer_sum = self.data_transfer_in + self.data_transfer_out
        log(f"data_transfer_in={self.data_transfer_in} MB => rounded={int(self.data_transfer_in)} MB")
        log(f"data_transfer_out={self.data_transfer_out} MB => rounded={int(self.data_transfer_out)} MB")
        log(f"data_transfer_sum={data_transfer_sum} MB => rounded={int(data_transfer_sum)} MB")
        self.process_payment_tx()
        log("SUCCESS")
        # TODO: garbage collector, removed downloaded code from local since it is not needed anymore


if __name__ == "__main__":
    kwargs = {
        "job_key": sys.argv[1],
        "index": sys.argv[2],
        "received_block_number": sys.argv[3],
        "folder_name": sys.argv[4],
        "slurm_job_id": sys.argv[5],
    }
    cloud_storage = ENDCODE(**kwargs)
    try:
        cloud_storage.run()
    except Exception as e:
        if type(e).__name__ != "QuietExit":
            _colorize_traceback(e)
        sys.exit(1)


# cmd = ["tar", "-N", self.modified_date, "-jcvf", self.output_file_name] + glob.glob("*")
# success, output = run(cmd)
# self.output_file_name = f"result-{PROVIDER_ID}-{self.job_key}-{self.index}.tar.gz"
"""Approach to upload as .tar.gz. Currently not used.
                remove_source_code()
                with open(f"{results_folder_prev}/modified_date.txt') as content_file:
                date = content_file.read().strip()
                cmd = ['tar', '-N', date, '-jcvf', self.output_file_name] + glob.glob("*")
                log.write(run(cmd))
                cmd = ['ipfs', 'add', results_folder + '/result.tar.gz']
                self.result_ipfs_hash = run(cmd)
                self.result_ipfs_hash = self.result_ipfs_hash.split(' ')[1]
                silent_remove(results_folder + '/result.tar.gz')
# ---------------
# cmd = ["tar", "-N", self.modified_date, "-jcvf", patch_file] + glob.glob("*")
# success, output = run(cmd)
# logging.info(output)

# self.remove_source_code()
# cmd: tar -jcvf result-$providerID-$index.tar.gz *
# cmd = ['tar', '-jcvf', self.output_file_name] + glob.glob("*")
# cmd = ["tar", "-N", self.modified_date, "-czfj", self.output_file_name] + glob.glob("*")
# success, output = run(cmd)
# logging.info(f"Files to be archived using tar: \n {output}")
"""
