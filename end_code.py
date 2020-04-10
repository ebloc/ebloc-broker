#!/usr/bin/env python3

import base64
import datetime
import getpass
import os
import subprocess
import sys
import time
from typing import List

from pymongo import MongoClient

import libs.eudat as eudat
import libs.gdrive as gdrive
import libs.git as git
import libs.ipfs as ipfs
import libs.mongodb as mongodb
import libs.slurm as slurm
from config import bp, load_log  # noqa: F401
from contractCalls.get_job_info import get_job_info, get_job_source_code_hashes
from contractCalls.get_requester_info import get_requester_info
from contractCalls.processPayment import processPayment
from imports import connect
from lib import (
    StorageID,
    calculate_folder_size,
    eblocbroker_function_call,
    get_ipfs_cumulative_size,
    ipfs_add,
    is_dir,
    job_state_code,
    remove_empty_files_and_folders,
    remove_files,
    run_command,
    run_command_stdout_to_file,
    silent_remove,
    subprocess_call,
)
from settings import WHERE, init_env
from utils import byte_to_mb, bytes32_to_ipfs, create_dir, eth_address_to_md5, read_json

eBlocBroker, w3 = connect()
mc = MongoClient()
env = init_env()


class ENDCODE:
    def __init__(self, **kwargs) -> None:
        global logging
        args = " ".join(["{!r}".format(v) for k, v in kwargs.items()])
        self.job_key = kwargs.pop("job_key")
        self.index = kwargs.pop("index")
        self.cloud_storage_id = kwargs.pop("cloud_storage_id")
        self.received_block_number = kwargs.pop("received_block_number")
        self.folder_name = kwargs.pop("folder_name")
        self.slurm_job_id = kwargs.pop("slurm_job_id")
        self.share_tokens = {}
        self.encoded_share_tokens = {}
        self.dataTransferIn = 0
        self.dataTransferOut = 0
        self.result_ipfs_hash = ""
        self.source_code_hashes_to_process: List[str] = []
        # https://stackoverflow.com/a/5971326/2402577 , https://stackoverflow.com/a/4453495/2402577
        # my_env = os.environ.copy();
        # my_env["IPFS_PATH"] = HOME + "/.ipfs"
        # print(my_env)
        os.environ["IPFS_PATH"] = f"{env.HOME}/.ipfs"
        logging = load_log(f"{env.LOG_PATH}/endCodeAnalyse/{self.job_key}_{self.index}.log")
        logging.info(f"=> Entered into {self.__class__.__name__} case.")
        logging.info(f"START: {datetime.datetime.now()}")
        self.job_id = 0  # TODO: should be mapped slurm_job_id
        logging.info(f"~/eBlocBroker/end_code.py {args}")
        logging.info(f"slurm_job_id={self.slurm_job_id}")
        if self.job_key == self.index:
            logging.error("job_key and index are same.")
            sys.exit(1)

        try:
            self.job_info = eblocbroker_function_call(
                lambda: get_job_info(
                    env.PROVIDER_ID, self.job_key, self.index, self.job_id, self.received_block_number,
                ),
                10,
            )
        except:
            sys.exit(1)

        requester_id = self.job_info["jobOwner"].lower()
        requester_id_address = eth_address_to_md5(requester_id)
        success, self.requester_info = get_requester_info(requester_id)
        self.results_folder_prev = f"{env.PROGRAM_PATH}/{requester_id_address}/{self.job_key}_{self.index}"
        if not is_dir(self.results_folder_prev):
            sys.exit(1)

        self.results_folder = f"{self.results_folder_prev}/JOB_TO_RUN"
        if not is_dir(self.results_folder):
            sys.exit(1)

        self.results_data_link = f"{self.results_folder_prev}/data_link"
        self.results_data_folder = f"{self.results_folder_prev}/data"
        self.private_dir = f"{env.PROGRAM_PATH}/{requester_id_address}/cache"
        self.patch_folder = f"{self.results_folder_prev}/patch"

        create_dir(self.patch_folder)
        remove_empty_files_and_folders(self.results_folder)

        logging.info(f"whoami: {getpass.getuser()} - {os.getegid()}")
        logging.info(f"home: {env.HOME}")
        logging.info(f"pwd: {os.getcwd()}")
        logging.info(f"results_folder: {self.results_folder}")
        logging.info(f"job_key: {self.job_key}")
        logging.info(f"index: {self.index}")
        logging.info(f"cloud_storage_id: {self.cloud_storage_id}")
        logging.info(f"folder_name: {self.folder_name}")
        logging.info(f"providerID: {env.PROVIDER_ID}")
        logging.info(f"requester_id_address: {requester_id_address}")
        logging.info(f"received: {self.job_info['received']}")

    def set_source_code_hashes_to_process(self):
        if self.cloud_storage_id == StorageID.IPFS.value or self.cloud_storage_id == StorageID.IPFS_MINILOCK.value:
            for source_code_hash in self.source_code_hashes:
                ipfs_hash = bytes32_to_ipfs(source_code_hash)
                self.source_code_hashes_to_process.append(ipfs_hash)
        else:
            for source_code_hash in self.source_code_hashes:
                self.source_code_hashes_to_process.append(w3.toText(source_code_hash))

    def ipfs_add_folder(self, folder_path):
        success, self.result_ipfs_hash = ipfs_add(folder_path)
        logging.info(f"result_ipfs_hash={self.result_ipfs_hash}")
        ipfs.pin(self.result_ipfs_hash)
        data_transfer_out = get_ipfs_cumulative_size(self.result_ipfs_hash)
        data_transfer_out = byte_to_mb(data_transfer_out)
        self.dataTransferOut += data_transfer_out
        return success

    def process_payment_tx(self):
        end_time_stamp = slurm.get_job_end_time(self.slurm_job_id)
        try:
            tx_hash = eblocbroker_function_call(
                lambda: processPayment(
                    self.job_key,
                    self.index,
                    self.job_id,
                    self.elapsed_raw_time,
                    self.result_ipfs_hash,
                    self.cloud_storage_id,
                    end_time_stamp,
                    self.dataTransferIn,
                    self.dataTransferOut,
                    self.job_info["core"],
                    self.job_info["executionDuration"],
                ),
                10,
            )
        except:
            sys.exit(1)

        logging.info(f"processPayment()_tx_hash={tx_hash}")
        f = open(f"{env.LOG_PATH}/transactions/{env.PROVIDER_ID}.txt", "a")
        f.write(f"{self.job_key}_{self.index} | [processPayment()] tx_hash: {tx_hash} |")
        f.close()

    def get_shared_tokens(self):
        try:
            data = read_json(f"{self.private_dir}/{self.job_key}_shareID.json")
            share_ids = data
        except:
            pass

        for source_code_hash in self.source_code_hashes_to_process:
            try:
                share_token = share_ids[source_code_hash]["share_token"]
                self.share_tkens[source_code_hash] = share_token
                self.encoded_share_tokens[source_code_hash] = base64.b64encode(
                    (f"{share_token}:").encode("utf-8")
                ).decode("utf-8")
            except KeyError:
                success, share_token = mongodb.find_key(mc["eBlocBroker"]["shareID"], self.job_key)
                self.share_tokens[source_code_hash] = share_token
                self.encoded_share_tokens[source_code_hash] = base64.b64encode(
                    (f"{share_token}:").encode("utf-8")
                ).decode("utf-8")
                if not success:
                    logging.error(f"E: share_id cannot detected from key: {self.job_key}")
                    return False
        if success:
            for key in share_ids:
                value = share_ids[key]
                encoded_value = self.encoded_share_tokens[key]
                logging.info(
                    "shared_tokens: ({}) => ({}) encoded:({})".format(key, value["share_token"], encoded_value)
                )

    def remove_source_code(self):
        """Client's initial downloaded files are removed."""
        timestamp_file = f"{self.results_folder_prev}/timestamp.txt"
        cmd = ["find", self.results_folder, "-type", "f", "!", "-newer", timestamp_file]
        success, files_to_remove = run_command(cmd, None, True)
        if not files_to_remove or files_to_remove:
            logging.info(f"Files to be removed: \n{files_to_remove}\n")

        subprocess.run(
            ["find", self.results_folder, "-type", "f", "!", "-newer", timestamp_file, "-delete",]
        )

    def git_diff_patch_and_upload(self, source, name, is_job_key) -> bool:
        if is_job_key:
            logging.info(f"patch_base={self.patch_folder}")
            logging.info(f"=> Patch for source code {name}")
        else:
            logging.info(f"=> Patch for data file {name}")

        try:
            self.patch_name, self.patch_file, is_file_empty = git.diff_patch(
                source, name, self.index, self.patch_folder, self.cloud_storage_id
            )
        except:
            return False

        if not is_file_empty:
            success = self._upload(source, name, is_job_key)
            if not success:
                return False
        return True

    def upload(self) -> bool:
        remove_files(f"{self.results_folder}/.node-xmlhttprequest*")
        success = self.git_diff_patch_and_upload(self.results_folder, self.job_key, is_job_key=True)
        if not success:
            return False

        for name in self.source_code_hashes_to_process[1:]:
            # starting from 1st index for data files
            source = f"{self.results_data_folder}/{name}"
            success = self.git_diff_patch_and_upload(source, name, is_job_key=False)
            if not success:
                return False
        return True

    def run(self):
        f = f"{self.results_folder_prev}/dataTransferIn.json"
        try:
            data = read_json(f)
            self.dataTransferIn = data["dataTransferIn"]
        except:
            logging.error("dataTransferIn.json does not exist...")

        logging.info(f"dataTransferIn={self.dataTransferIn} MB => rounded={int(self.dataTransferIn)} MB")

        f = f"{self.results_folder_prev}/modified_date.txt"
        if os.path.isfile(f):
            f = open(f, "r")
            self.modified_date = f.read().rstrip()
            f.close()
            logging.info(f"modified_date={self.modified_date}")

        self.minilock_id = self.requester_info["miniLockID"]
        logging.info("jobOwner's Info: ")
        logging.info("{0: <12}".format("email:") + self.requester_info["email"])
        logging.info("{0: <12}".format("miniLockID:") + self.minilock_id)
        logging.info("{0: <12}".format("ipfsID:") + self.requester_info["ipfsID"])
        logging.info("{0: <12}".format("fID:") + self.requester_info["fID"])
        logging.info("")

        if self.job_info["jobStateCode"] == str(job_state_code["COMPLETED"]):
            logging.error("Job is completed and already get paid.")
            sys.exit(1)

        executionDuration = self.job_info["executionDuration"]
        logging.info(f"requested_execution_duration={executionDuration[self.job_id]} minutes")

        for attempt in range(10):
            if self.job_info["jobStateCode"] == job_state_code["RUNNING"]:
                # it will come here eventually, when setJob() is deployed.
                logging.info("Job has been started.")
                break  # wait until does values updated on the blockchain

            if self.job_info["jobStateCode"] == job_state_code["COMPLETED"]:
                # detects an error on the SLURM side
                logging.warning("E: Job is already completed job and its money is received.")
                sys.exit(1)

            try:
                self.job_info = eblocbroker_function_call(
                    lambda: get_job_info(
                        env.PROVIDER_ID, self.job_key, self.index, self.job_id, self.received_block_number,
                    ),
                    10,
                )
            except:
                sys.exit(1)

            logging.info(f"Waiting for {attempt * 15} seconds to pass...")
            # short sleep here so this loop is not keeping CPU busy due to setJobSuccess may deploy late
            time.sleep(15)
        else:  # failed all the attempts - abort
            sys.exit(1)

        try:
            self.job_info = eblocbroker_function_call(
                lambda: get_job_source_code_hashes(
                    self.job_info, env.PROVIDER_ID, self.job_key, self.index, self.job_id, self.received_block_number,
                ),
                10,
            )
        except:
            sys.exit(1)

        self.source_code_hashes = self.job_info["sourceCodeHash"]
        self.set_source_code_hashes_to_process()
        cmd = ["scontrol", "show", "job", self.slurm_job_id]
        run_command_stdout_to_file(cmd, f"{self.results_folder}/slurmJobInfo.out")
        self.elapsed_raw_time = slurm.get_elapsed_raw_time(self.slurm_job_id)
        if self.elapsed_raw_time > int(executionDuration[self.job_id]):
            self.elapsed_raw_time = executionDuration[self.job_id]

        logging.info(f"finalized_elapsed_raw_time={self.elapsed_raw_time}")
        logging.info(f"job_info={self.job_info}")
        if not self.run_upload():
            return False

        dataTransferSum = self.dataTransferIn + self.dataTransferOut
        logging.info(f"dataTransferIn={self.dataTransferIn} MB => rounded={int(self.dataTransferIn)} MB")
        logging.info(f"dataTransferOut={self.dataTransferOut} MB => rounded={int(self.dataTransferOut)} MB")
        logging.info(f"dataTransferSum={dataTransferSum} MB => rounded={int(dataTransferSum)} MB")
        self.process_payment_tx()
        logging.info("COMPLETED")
        # TODO; garbage collector: Removed downloaded code from local since it is not needed anymore


class IpfsMiniLockClass(ENDCODE):
    def __init__(self, **kwargs) -> None:
        super(self.__class__, self).__init__(**kwargs)

    def run_upload(self):
        self.upload()
        # it will upload files after all the patchings are completed
        return self.ipfs_add_folder(self.patch_folder)

    def _upload(self, path, source_code_hash, is_job_key) -> bool:
        os.chdir(self.results_folder)
        cmd = [
            "mlck",
            "encrypt",
            "-f",
            self.patch_file,
            self.minilock_id,
            "--anonymous",
            f"--output-file={self.patch_file}.minilock",
        ]
        success, output = run_command(cmd, my_env=None, is_exit_flag=True)
        logging.info(output)
        if success:
            silent_remove(self.patch_file)
        return success


class IpfsClass(ENDCODE):
    def __init__(self, **kwargs) -> None:
        super(self.__class__, self).__init__(**kwargs)

    def run_upload(self):
        success = self.upload()
        # it will upload files after all the patchings are completed
        success = self.ipfs_add_folder(self.patch_folder)
        return success

    def _upload(self, path, source_code_hash, is_job_key) -> bool:
        """It will upload after all patchings are completed"""
        return True


class EudatClass(ENDCODE):
    def __init__(self, **kwargs) -> None:
        super(self.__class__, self).__init__(**kwargs)

    def run_upload(self):
        self.get_shared_tokens()
        return self.upload()

    def _upload(self, path, source_code_hash, is_job_key) -> bool:
        data_transfer_out = calculate_folder_size(self.patch_file)
        logging.info(f"[{source_code_hash}]'s dataTransferOut => {data_transfer_out} MB")
        self.dataTransferOut += data_transfer_out
        success = eudat.upload_results(
            self.encoded_share_tokens[source_code_hash], self.patch_name, self.results_folder_prev, 5,
        )
        return success


class GdriveClass(ENDCODE):
    def __init__(self, **kwargs) -> None:
        super(self.__class__, self).__init__(**kwargs)

    def run_upload(self) -> bool:
        return self.upload()

    def _upload(self, path, key, is_job_key) -> bool:
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

        self.dataTransferOut += calculate_folder_size(self.patch_file)
        logging.info(f"dataTransferOut={self.dataTransferOut} MB => rounded={int(self.dataTransferOut)} MB")
        if "folder" in mime_type:
            cmd = [
                env.GDRIVE,
                "upload",
                "--parent",
                key,
                self.patch_file,
                "-c",
                env.GDRIVE_METADATA,
            ]
        elif "gzip" in mime_type or "/zip" in mime_type:
            cmd = [
                env.GDRIVE,
                "update",
                key,
                self.patch_file,
                "-c",
                env.GDRIVE_METADATA,
            ]
        else:
            logging.error("E: Files could not be uploaded")
            return False

        try:
            logging.info(subprocess_call(cmd, 5))
        except:
            logging.error(f"[{env.WHERE(1)}] E: gdrive could not upload the file")
            return False

        return True


if __name__ == "__main__":
    _cloud_storage_id = int(sys.argv[3])
    kwargs = {
        "job_key": sys.argv[1],
        "index": sys.argv[2],
        "cloud_storage_id": _cloud_storage_id,
        "received_block_number": sys.argv[4],
        "folder_name": sys.argv[5],
        "slurm_job_id": sys.argv[6],
    }

    if _cloud_storage_id == StorageID.GDRIVE.value:
        cloud_storage = GdriveClass(**kwargs)
    elif _cloud_storage_id == StorageID.EUDAT.value:
        cloud_storage = EudatClass(**kwargs)
    elif _cloud_storage_id == StorageID.IPFS.value:
        cloud_storage = IpfsClass(**kwargs)
    elif _cloud_storage_id == StorageID.IPFS_MINILOCK.value:
        cloud_storage = IpfsMiniLockClass(**kwargs)

    cloud_storage.run()


# cmd = ["tar", "-N", self.modified_date, "-jcvf", self.output_file_name] + glob.glob("*")
# success, output = run_command(cmd, None, True)
# logging.info(output)
# self.output_file_name = f"result-{PROVIDER_ID}-{self.job_key}-{self.index}.tar.gz"
""" Approach to upload as .tar.gz. Currently not used.
                remove_source_code()
                with open(f"{results_folder_prev}/modified_date.txt') as content_file:
                date = content_file.read().strip()
                cmd = ['tar', '-N', date, '-jcvf', self.output_file_name] + glob.glob("*")
                log.write(run_command(cmd, None, True))
                cmd = ['ipfs', 'add', results_folder + '/result.tar.gz']
                success, self.result_ipfs_hash = run_command(cmd)
                self.result_ipfs_hash = self.result_ipfs_hash.split(' ')[1]
                silent_remove(results_folder + '/result.tar.gz')
"""
# cmd = ["tar", "-N", self.modified_date, "-jcvf", patch_file] + glob.glob("*")
# success, output = run_command(cmd, None, True)
# logging.info(output)
# time.sleep(0.1)

# self.remove_source_code()
# cmd: tar -jcvf result-$providerID-$index.tar.gz *
# cmd = ['tar', '-jcvf', self.output_file_name] + glob.glob("*")
# cmd = ["tar", "-N", self.modified_date, "-czfj", self.output_file_name] + glob.glob("*")
# success, output = run_command(cmd, None, True)
# logging.info(f"Files to be archived using tar: \n {output}")
