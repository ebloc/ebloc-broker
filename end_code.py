#!/usr/bin/env python3

import base64
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
from config import bp, env, load_log  # noqa: F401
from contractCalls.get_job_info import get_job_info, get_job_source_code_hashes
from contractCalls.get_requester_info import get_requester_info
from contractCalls.process_payment import process_payment
from imports import connect
from lib import (
    WHERE,
    StorageID,
    calculate_folder_size,
    eblocbroker_function_call,
    is_dir,
    job_state_code,
    log,
    remove_empty_files_and_folders,
    remove_files,
    run,
    run_command_stdout_to_file,
    silent_remove,
    subprocess_call,
)
from utils import (
    _colorize_traceback,
    byte_to_mb,
    bytes32_to_ipfs,
    create_dir,
    eth_address_to_md5,
    is_dir_empty,
    read_file,
    read_json,
)

eBlocBroker, w3 = connect()
mc = MongoClient()


class IpfsMiniLock(object):
    def initialize(self):
        pass

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
        try:
            logging.info(run(cmd))
        except:
            sys.exit(1)

        silent_remove(self.patch_file)
        return True


class Ipfs(object):
    def initialize(self):
        pass

    def _upload(self, path, source_code_hash, is_job_key) -> bool:
        """It will upload after all patchings are completed"""
        return True


class Eudat(object):
    def initialize(self):
        self.get_shared_tokens()

    def _upload(self, path, source_code_hash, is_job_key) -> bool:
        data_transfer_out = calculate_folder_size(self.patch_file)
        logging.info(f"[{source_code_hash}]'s dataTransferOut => {data_transfer_out} MB")
        self.dataTransferOut += data_transfer_out
        success = eudat.upload_results(
            self.encoded_share_tokens[source_code_hash], self.patch_name, self.results_folder_prev, 5,
        )
        return success


class Gdrive(object):
    def initialize(self):
        pass

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


class ENDCODE(IpfsMiniLock, Ipfs, Eudat, Gdrive):
    def __init__(self, **kwargs) -> None:
        global logging
        args = " ".join(["{!r}".format(v) for k, v in kwargs.items()])
        self.job_key = kwargs.pop("job_key")
        self.index = kwargs.pop("index")
        self.received_block_number = kwargs.pop("received_block_number")
        self.folder_name = kwargs.pop("folder_name")
        self.slurm_job_id = kwargs.pop("slurm_job_id")
        self.share_tokens = {}
        self.encoded_share_tokens = {}
        self.dataTransferIn = 0
        self.dataTransferOut = 0
        self.source_code_hashes_to_process: List[str] = []
        self.result_ipfs_hash = ""

        # https://stackoverflow.com/a/5971326/2402577 , https://stackoverflow.com/a/4453495/2402577
        # my_env = os.environ.copy();
        # my_env["IPFS_PATH"] = HOME + "/.ipfs"
        # print(my_env)
        os.environ["IPFS_PATH"] = f"{env.HOME}/.ipfs"
        logging = load_log(f"{env.LOG_PATH}/endCodeAnalyse/{self.job_key}_{self.index}.log")
        # logging.info(f"=> Entered into {self.__class__.__name__} case.") # delete
        # logging.info(f"START: {datetime.datetime.now()}") # delete
        self.job_id = 0  # TODO: should be mapped slurm_job_id

        log(f"~/eBlocBroker/end_code.py {args}", "blue")
        log(f"slurm_job_id={self.slurm_job_id}", "white")
        if self.job_key == self.index:
            logging.error("job_key and index are same")
            sys.exit(1)

        try:
            self.job_info = eblocbroker_function_call(
                lambda: get_job_info(
                    env.PROVIDER_ID, self.job_key, self.index, self.job_id, self.received_block_number,
                ),
                10,
            )
            self.cloud_storage_ids = self.job_info["cloudStorageID"]
            requester_id = self.job_info["jobOwner"].lower()
            requester_id_address = eth_address_to_md5(requester_id)
            self.requester_info = get_requester_info(requester_id)
        except:
            sys.exit(1)

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
        self.patch_folder_ipfs = f"{self.results_folder_prev}/patch_ipfs"

        create_dir(self.patch_folder)
        create_dir(self.patch_folder_ipfs)

        remove_empty_files_and_folders(self.results_folder)

        log(f"whoami: {getpass.getuser()} - {os.getegid()}", "white")
        log(f"home: {env.HOME}", "white")
        log(f"pwd: {os.getcwd()}", "white")
        log(f"results_folder: {self.results_folder}", "white")
        log(f"job_key: {self.job_key}", "white")
        log(f"index: {self.index}", "white")
        log(f"cloud_storage_ids: {self.cloud_storage_ids}", "white")
        log(f"folder_name: {self.folder_name}", "white")
        log(f"providerID: {env.PROVIDER_ID}", "white")
        log(f"requester_id_address: {requester_id_address}", "white")
        log(f"received: {self.job_info['received']}", "white")

    def get_cloud_storage_class(self, _id):
        """Returns cloud storage used for the id of the data"""
        if self.cloud_storage_ids[_id] == StorageID.IPFS.value:
            return Ipfs
        elif self.cloud_storage_ids[_id] == StorageID.IPFS_MINILOCK.value:
            return IpfsMiniLock
        elif self.cloud_storage_ids[_id] == StorageID.EUDAT.value:
            return Eudat
        elif self.cloud_storage_ids[_id] == StorageID.GDRIVE.value:
            return Gdrive

    def set_source_code_hashes_to_process(self):
        for idx, source_code_hash in enumerate(self.source_code_hashes):
            if (
                self.cloud_storage_ids[idx] == StorageID.IPFS.value
                or self.cloud_storage_ids[idx] == StorageID.IPFS_MINILOCK.value
            ):
                ipfs_hash = bytes32_to_ipfs(source_code_hash)
                self.source_code_hashes_to_process.append(ipfs_hash)
            else:
                self.source_code_hashes_to_process.append(w3.toText(source_code_hash))

    def ipfs_add_folder(self, folder_path):
        try:
            success, self.result_ipfs_hash = ipfs.add(folder_path)
            logging.info(f"result_ipfs_hash={self.result_ipfs_hash}")
            ipfs.pin(self.result_ipfs_hash)
            data_transfer_out = ipfs.get_cumulative_size(self.result_ipfs_hash)
        except:
            logging.error(_colorize_traceback())
            sys.exit()

        data_transfer_out = byte_to_mb(data_transfer_out)
        self.dataTransferOut += data_transfer_out
        return success

    def process_payment_tx(self):
        try:
            end_time_stamp = slurm.get_job_end_time(self.slurm_job_id)
            tx_hash = eblocbroker_function_call(
                lambda: process_payment(
                    self.job_key,
                    self.index,
                    self.job_id,
                    self.elapsed_raw_time,
                    self.result_ipfs_hash,
                    self.cloud_storage_ids,
                    end_time_stamp,
                    self.dataTransferIn,
                    self.dataTransferOut,
                    self.job_info["core"],
                    self.job_info["executionDuration"],
                ),
                10,
            )
            logging.info(tx_hash)
        except:
            sys.exit(1)

        f = open(f"{env.LOG_PATH}/transactions/{env.PROVIDER_ID}.txt", "a")
        f.write(f"processPayment {self.job_key} {self.index} {tx_hash}")
        f.close()

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
                success, share_token = mongodb.find_key(mc["eBlocBroker"]["shareID"], self.job_key)
                self.share_tokens[source_code_hash] = share_token
                self.encoded_share_tokens[source_code_hash] = base64.b64encode(
                    (f"{share_token}:").encode("utf-8")
                ).decode("utf-8")
                if not success:
                    logging.error(f"E: share_id cannot detected from key: {self.job_key}")
                    return False

        for key in share_ids:
            value = share_ids[key]
            encoded_value = self.encoded_share_tokens[key]
            logging.info("shared_tokens: ({}) => ({}) encoded:({})".format(key, value["share_token"], encoded_value))

    def remove_source_code(self):
        """Client's initial downloaded files are removed."""
        timestamp_file = f"{self.results_folder_prev}/timestamp.txt"
        cmd = ["find", self.results_folder, "-type", "f", "!", "-newer", timestamp_file]
        try:
            files_to_remove = run(cmd)
        except:
            sys.exit()
        if not files_to_remove or files_to_remove:
            logging.info(f"Files to be removed: \n{files_to_remove}\n")

        subprocess.run(
            ["find", self.results_folder, "-type", "f", "!", "-newer", timestamp_file, "-delete",]
        )

    def git_diff_patch_and_upload(self, source, name, storage_class, is_job_key) -> bool:
        if is_job_key:
            logging.info(f"patch_base={self.patch_folder}")
            logging.info(f"=> Patch for source code {name}")
        else:
            logging.info(f"=> Patch for data file {name}")

        try:
            if storage_class is Ipfs or storage_class is IpfsMiniLock:
                target_path = self.patch_folder_ipfs
            else:
                target_path = self.patch_folder

            self.patch_name, self.patch_file, is_file_empty = git.diff_patch(source, name, self.index, target_path)
        except:
            raise

        if not is_file_empty:
            if not storage_class._upload(self, source, name, is_job_key):
                raise

    def upload(self) -> bool:
        remove_files(f"{self.results_folder}/.node-xmlhttprequest*")
        try:
            storage_class = self.get_cloud_storage_class(0)
            self.git_diff_patch_and_upload(self.results_folder, self.job_key, storage_class, is_job_key=True)
        except:
            return False

        for idx, name in enumerate(self.source_code_hashes_to_process[1:], 1):
            # starting from 1st index for data files
            source = f"{self.results_data_folder}/{name}"
            storage_class = self.get_cloud_storage_class(idx)
            try:
                self.git_diff_patch_and_upload(source, name, storage_class, is_job_key=False)
            except:
                return False

        if not is_dir_empty(self.patch_folder_ipfs):
            # it will upload files after all the patchings are completed
            # in case any file is created via ipfs
            return self.ipfs_add_folder(self.patch_folder_ipfs)

        return True

    def run(self):
        try:
            data = read_json(f"{self.results_folder_prev}/dataTransferIn.json")
            self.dataTransferIn = data["dataTransferIn"]
            logging.info(f"dataTransferIn={self.dataTransferIn} MB => rounded={int(self.dataTransferIn)} MB")
        except:
            logging.error("E: dataTransferIn.json does not exist")

        try:
            self.modified_date = read_file(f"{self.results_folder_prev}/modified_date.txt")
            logging.info(f"modified_date={self.modified_date}")
        except:
            logging.error("E: modified_date.txt file couldn't be read")

        self.minilock_id = self.requester_info["miniLockID"]
        logging.info("job_owner's info: --------------------------------------------")
        logging.info("{0: <12}".format("email:") + self.requester_info["email"])
        logging.info("{0: <12}".format("miniLockID:") + self.minilock_id)
        logging.info("{0: <12}".format("ipfsID:") + self.requester_info["ipfsID"])
        logging.info("{0: <12}".format("fID:") + self.requester_info["fID"])
        logging.info("-------------------------------------------------------------")

        if self.job_info["jobStateCode"] == str(job_state_code["COMPLETED"]):
            logging.error("Job is completed and already get paid")
            sys.exit(1)

        execution_duration = self.job_info["executionDuration"]
        logging.info(f"requested_execution_duration={execution_duration[self.job_id]} minutes")
        for attempt in range(10):
            if self.job_info["jobStateCode"] == job_state_code["RUNNING"]:
                # it will come here eventually, when setJob() is deployed
                logging.warning("Job has been started.")
                break  # wait until does values updated on the blockchain

            if self.job_info["jobStateCode"] == job_state_code["COMPLETED"]:
                # detects an error on the slurm side
                logging.warning("Job is already completed job and its money is received")
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
        if self.elapsed_raw_time > int(execution_duration[self.job_id]):
            self.elapsed_raw_time = execution_duration[self.job_id]

        logging.info(f"finalized_elapsed_raw_time={self.elapsed_raw_time}")
        logging.info(f"job_info={self.job_info}")

        initial_storage_class = self.get_cloud_storage_class(0)
        initial_storage_class.initialize(self)
        if not self.upload():
            return False

        data_transfer_sum = self.dataTransferIn + self.dataTransferOut
        logging.info(f"dataTransferIn={self.dataTransferIn} MB => rounded={int(self.dataTransferIn)} MB")
        logging.info(f"dataTransferOut={self.dataTransferOut} MB => rounded={int(self.dataTransferOut)} MB")
        logging.info(f"data_transfer_sum={data_transfer_sum} MB => rounded={int(data_transfer_sum)} MB")
        self.process_payment_tx()
        logging.info("All done!")
        # TODO; garbage collector: Removed downloaded code from local since it is not needed anymore


if __name__ == "__main__":
    kwargs = {
        "job_key": sys.argv[1],
        "index": sys.argv[2],
        "received_block_number": sys.argv[3],
        "folder_name": sys.argv[4],
        "slurm_job_id": sys.argv[5],
    }

    cloud_storage = ENDCODE(**kwargs)
    cloud_storage.run()

# cmd = ["tar", "-N", self.modified_date, "-jcvf", self.output_file_name] + glob.glob("*")
# success, output = run(cmd)
# logging.info(output)
# self.output_file_name = f"result-{PROVIDER_ID}-{self.job_key}-{self.index}.tar.gz"
""" Approach to upload as .tar.gz. Currently not used.
                remove_source_code()
                with open(f"{results_folder_prev}/modified_date.txt') as content_file:
                date = content_file.read().strip()
                cmd = ['tar', '-N', date, '-jcvf', self.output_file_name] + glob.glob("*")
                log.write(run_command(cmd))
                cmd = ['ipfs', 'add', results_folder + '/result.tar.gz']
                success, self.result_ipfs_hash = run_command(cmd)
                self.result_ipfs_hash = self.result_ipfs_hash.split(' ')[1]
                silent_remove(results_folder + '/result.tar.gz')
"""
# cmd = ["tar", "-N", self.modified_date, "-jcvf", patch_file] + glob.glob("*")
# success, output = run(cmd)
# logging.info(output)
# time.sleep(0.1)

# self.remove_source_code()
# cmd: tar -jcvf result-$providerID-$index.tar.gz *
# cmd = ['tar', '-jcvf', self.output_file_name] + glob.glob("*")
# cmd = ["tar", "-N", self.modified_date, "-czfj", self.output_file_name] + glob.glob("*")
# success, output = run(cmd)
# logging.info(f"Files to be archived using tar: \n {output}")
