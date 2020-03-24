#!/usr/bin/env python3

import base64
import datetime
import getpass
import glob
import os
import subprocess
import sys
import time
from typing import List

from pymongo import MongoClient

import lib
from config import bp, load_log  # noqa: F401
from contractCalls.get_job_info import get_job_info, get_job_source_code_hashes
from contractCalls.get_requester_info import get_requester_info
from contractCalls.processPayment import processPayment
from imports import connect
from lib import (GDRIVE, GDRIVE_METADATA, HOME, LOG_PATH, PROGRAM_PATH,
                 PROVIDER_ID, StorageID, eblocbroker_function_call, ipfs_add,
                 remove_empty_files_and_folders, run_command,
                 run_command_stdout_to_file)
from lib_gdrive import get_gdrive_file_info
from lib_git import git_diff_patch
from lib_mongodb import find_key
from lib_owncloud import upload_results_to_eudat
from utils import byte_to_mb, eth_address_to_md5, read_json

eBlocBroker, w3 = connect()
mc = MongoClient()


class ENDCODE:
    def __init__(
        self, _job_key, _index, _cloud_storage_id, _received_block_number, _folder_name, _slurm_job_id,
    ) -> None:
        global logging
        self.job_key = _job_key
        self.index = _index
        self.cloud_storage_id = _cloud_storage_id
        self.received_block_number = _received_block_number
        self.folder_name = _folder_name
        self.slurm_job_id = _slurm_job_id
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
        os.environ["IPFS_PATH"] = f"{HOME}/.ipfs"
        logging = load_log(f"{LOG_PATH}/endCodeAnalyse/{self.job_key}_{self.index}.log")
        logging.info(f"START: {datetime.datetime.now()}")
        self.job_id = 0  # TODO: should be mapped slurm_job_id
        logging.info(
            f"~/eBlocBroker/end_code.py {self.job_key} {self.index} {self.cloud_storage_id} {self.received_block_number} {self.folder_name} {self.slurm_job_id}"
        )
        logging.info(f"slurm_job_id={self.slurm_job_id}")
        if self.job_key == self.index:
            logging.error("job_key and index are same.")
            sys.exit(1)

        success, self.job_info = eblocbroker_function_call(
            lambda: get_job_info(PROVIDER_ID, self.job_key, self.index, self.job_id, self.received_block_number,), 10,
        )
        if not success:
            sys.exit(1)

        requester_id = self.job_info["jobOwner"].lower()
        requester_id_address = eth_address_to_md5(requester_id)
        success, self.requester_info = get_requester_info(requester_id)
        self.results_folder_prev = f"{PROGRAM_PATH}/{requester_id_address}/{self.job_key}_{self.index}"
        self.results_folder = f"{self.results_folder_prev}/JOB_TO_RUN"
        self.results_data_link = f"{self.results_folder_prev}/data_link"
        self.results_data_folder = f"{self.results_folder_prev}/data"
        self.private_dir = f"{PROGRAM_PATH}/{requester_id_address}/cache"

        remove_empty_files_and_folders(self.results_folder)

        logging.info(f"whoami: {getpass.getuser()} - {os.getegid()}")
        logging.info(f"home: {HOME}")
        logging.info(f"pwd: {os.getcwd()}")
        logging.info(f"results_folder: {self.results_folder}")
        logging.info(f"job_key: {self.job_key}")
        logging.info(f"index: {self.index}")
        logging.info(f"cloud_storage_id: {self.cloud_storage_id}")
        logging.info(f"folder_name: {self.folder_name}")
        logging.info(f"providerID: {PROVIDER_ID}")
        logging.info(f"requester_id_address: {requester_id_address}")
        logging.info(f"received: {self.job_info['received']}")

    def process_payment_tx(self):
        # cmd: scontrol show job slurm_job_id | grep 'EndTime'| grep -o -P '(?<=EndTime=).*(?= )'
        success, output = run_command(["scontrol", "show", "job", self.slurm_job_id], None, True)
        p1 = subprocess.Popen(["echo", output], stdout=subprocess.PIPE)
        p2 = subprocess.Popen(["grep", "EndTime"], stdin=p1.stdout, stdout=subprocess.PIPE)
        p1.stdout.close()
        p3 = subprocess.Popen(["grep", "-o", "-P", "(?<=EndTime=).*(?= )"], stdin=p2.stdout, stdout=subprocess.PIPE,)
        p2.stdout.close()
        date = p3.communicate()[0].decode("utf-8").strip()

        cmd = ["date", "-d", date, "+'%s'"]  # cmd: date -d 2018-09-09T21:50:51 +"%s"
        success, end_time_stamp = run_command(cmd, None, True)
        end_time_stamp = end_time_stamp.rstrip().replace("'", "")
        logging.info(f"end_time_stamp={end_time_stamp}")

        success, tx_hash = eblocbroker_function_call(
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
        if not success:
            sys.exit(1)

        logging.info(f"processPayment()_tx_hash={tx_hash}")
        f = open(f"{LOG_PATH}/transactions/{PROVIDER_ID}.txt", "a")
        f.write(f"{self.job_key}_{self.index} | tx_hash: {tx_hash} | process_payment_tx()")
        f.close()

    def get_shared_tokens(self):
        success, data = read_json(f"{self.private_dir}/{self.job_key}_shareID.json")
        if success:
            share_ids = data

        for source_code_hash in self.source_code_hashes_to_process:
            try:
                share_token = share_ids[source_code_hash]["share_token"]
                self.share_tokens[source_code_hash] = share_token
                self.encoded_share_tokens[source_code_hash] = base64.b64encode((f"{share_token}:").encode("utf-8")).decode("utf-8")
            except KeyError:
                success, share_token = find_key(mc["eBlocBroker"]["shareID"], self.job_key)
                self.share_tokens[source_code_hash] = share_token
                self.encoded_share_tokens[source_code_hash] = base64.b64encode((f"{share_token}:").encode("utf-8")).decode("utf-8")
                if not success:
                    logging.error(f"E: share_id cannot detected from key: {self.job_key}")
                    return False

        if success:
            for key in share_ids:
                value = share_ids[key]
                encoded_value = self.encoded_share_tokens[key]
                logging.info("shared_tokens: ({}) => ({}) encoded:({})".format(key, value["share_token"], encoded_value))

    def remove_source_code(self):
        """Client's initial downloaded files are removed."""
        timestamp_file = f"{self.results_folder_prev}/timestamp.txt"
        cmd = ["find", self.results_folder, "-type", "f", "!", "-newer", timestamp_file]
        success, files_to_remove = run_command(cmd, None, True)
        if not files_to_remove or files_to_remove is not None:
            logging.info(f"Files to be removed: \n{files_to_remove}\n")

        subprocess.run(
            ["find", self.results_folder, "-type", "f", "!", "-newer", timestamp_file, "-delete",]
        )

    def ipfs_upload(self):
        # TODO:
        git_diff_patch()
        success, self.result_ipfs_hash = ipfs_add(self.results_folder)

        # self.dataTransferOut = lib.calculate_folder_size(results_folder)
        # log.write('dataTransferOut=' + str(self.dataTransferOut) + ' MB => rounded=' + str(int(self.dataTransferOut)) + ' MB')
        success, self.result_ipfs_hash = lib.get_ipfs_parent_hash(self.result_ipfs_hash)
        cmd = ["ipfs", "pin", "add", self.result_ipfs_hash]
        success, output = run_command(cmd, None, True)  # pin downloaded ipfs hash
        print(output)

        cmd = ["ipfs", "object", "stat", self.result_ipfs_hash]
        success, is_ipfs_hash_exist = run_command(cmd, None, True)  # pin downloaded ipfs hash
        for item in is_ipfs_hash_exist.split("\n"):
            if "CumulativeSize" in item:
                self.dataTransferOut = item.strip().split()[1]
                break

        self.dataTransferOut = byte_to_mb(self.dataTransferOut)
        logging.info(f"dataTransferOut={self.dataTransferOut} MB => rounded={int(self.dataTransferOut)} MB")

    def ipfs_minilock_upload(self):
        os.chdir(self.results_folder)
        cmd = ["tar", "-N", self.modified_date, "-jcvf", self.output_file_name,] + glob.glob("*")
        success, output = run_command(cmd, None, True)
        logging.info(output)

        cmd = [
            "mlck",
            "encrypt",
            "-f",
            f"{self.results_folder}/result.tar.gz",
            self.minilock_id,
            "--anonymous",
            f"--output-file={self.results_folder}/result.tar.gz.minilock",
        ]
        success, output = run_command(cmd, None, True)
        logging.info(output)

        # TODO:
        git_diff_patch()

        success, self.result_ipfs_hash = ipfs_add(f"{self.results_folder}/result.tar.gz.minilock")
        logging.info(f"result_ipfs_hash={self.result_ipfs_hash}")

        # self.dataTransferOut = lib.calculate_folder_size(results_folder + '/result.tar.gz.minilock')
        # log.write('dataTransferOut=' + str(self.dataTransferOut) + ' MB => rounded=' + str(int(self.dataTransferOut)) + ' MB')
        cmd = ["ipfs", "pin", "add", self.result_ipfs_hash]
        success, output = run_command(cmd, None, True)
        print(output)
        cmd = ["ipfs", "object", "stat", self.result_ipfs_hash]
        success, is_ipfs_hash_exist = run_command(cmd, None, True)
        for item in is_ipfs_hash_exist.split("\n"):
            if "CumulativeSize" in item:
                self.dataTransferOut = item.strip().split()[1]
                break

        self.dataTransferOut = byte_to_mb(self.dataTransferOut)
        logging.info(f"dataTransferOut={self.dataTransferOut} MB => rounded={int(self.dataTransferOut)} MB")

    """
    def gdrive_upload(self):
        lib.remove_files(f"{self.results_folder}/.node-xmlhttprequest*")
        success = self._gdrive_upload(self.results_folder, self.job_key)
        if not success:
            return False

        for data_name in self.source_code_hashes_to_process[1:]:
            # starting from 1st index for data files
            logging.info(f"=> Patch for data {data_name}")
            data_path = f"{self.results_data_folder}/{data_name}"
            bp()
            success = self._gdrive_upload(data_path, data_name)
            if not success:
                return False
        return True
    """

    def upload(self) -> bool:
        lib.remove_files(f"{self.results_folder}/.node-xmlhttprequest*")
        success = self._upload(self.results_folder, self.job_key)
        if not success:
            return False

        for data_name in self.source_code_hashes_to_process[1:]:
            # starting from 1st index for data files
            logging.info(f"=> Patch for data {data_name}")
            data_path = f"{self.results_data_folder}/{data_name}"
            success = self._upload(data_path, data_name)
            bp()
            if not success:
                return False
        return True

    def run(self):
        f = f"{self.results_folder_prev}/dataTransferIn.json"
        success, data = read_json(f)
        if success:
            self.dataTransferIn = data["dataTransferIn"]
        else:
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

        if self.job_info["jobStateCode"] == str(lib.job_state_code["COMPLETED"]):
            logging.error("Job is completed and already get paid.")
            sys.exit(1)

        executionDuration = self.job_info["executionDuration"]
        logging.info(f"requested_execution_duration={executionDuration[self.job_id]} minutes")

        for attempt in range(10):
            if self.job_info["jobStateCode"] == lib.job_state_code["RUNNING"]:
                # It will come here eventually, when setJob() is deployed.
                logging.info("Job has been started.")
                break  # Wait until does values updated on the blockchain

            if self.job_info["jobStateCode"] == lib.job_state_code["COMPLETED"]:
                # Detects an error on the SLURM side
                logging.warning("E: Job is already completed job and its money is received.")
                sys.exit(1)

            success, self.job_info = eblocbroker_function_call(
                lambda: get_job_info(PROVIDER_ID, self.job_key, self.index, self.job_id, self.received_block_number,),
                10,
            )
            if not success:
                sys.exit(1)

            logging.info(f"Waiting for {attempt * 15} seconds to pass...")
            # Short sleep here so this loop is not keeping CPU busy //setJobSuccess may deploy late.
            time.sleep(15)
        else:
            # Failed all the attempts - abort
            sys.exit(1)

        success, self.job_info = eblocbroker_function_call(
            # sourceCodeHashes of the completed job is obtained from its event
            lambda: get_job_source_code_hashes(
                self.job_info, PROVIDER_ID, self.job_key, self.index, self.job_id, self.received_block_number,
            ),
            10,
        )
        if not success:
            sys.exit(1)

        self.source_code_hashes = self.job_info["sourceCodeHash"]
        for source_code_hash in self.source_code_hashes:
            self.source_code_hashes_to_process.append(w3.toText(source_code_hash))

        logging.info(f"job_name={self.folder_name}")
        cmd = ["scontrol", "show", "job", self.slurm_job_id]
        success = run_command_stdout_to_file(cmd, f"{self.results_folder}/slurmJobInfo.out")
        # cmd: sacct -n -X -j $slurm_job_id --format="Elapsed"
        cmd = ["sacct", "-n", "-X", "-j", self.slurm_job_id, "--format=Elapsed"]
        success, elapsed_time = run_command(cmd, None, True)
        logging.info(f"ElapsedTime={elapsed_time}")
        elapsed_time = elapsed_time.split(":")
        elapsed_day = "0"
        elapsed_hour = elapsed_time[0].strip()
        elapsed_minute = elapsed_time[1].rstrip()

        if "-" in str(elapsed_hour):
            elapsed_hour = elapsed_hour.split("-")
            elapsed_day = elapsed_hour[0]
            elapsed_hour = elapsed_hour[1]

        self.elapsed_raw_time = int(elapsed_day) * 1440 + int(elapsed_hour) * 60 + int(elapsed_minute) + 1
        logging.info(f"ElapsedRawTime={self.elapsed_raw_time}")

        if self.elapsed_raw_time > int(executionDuration[self.job_id]):
            self.elapsed_raw_time = executionDuration[self.job_id]

        logging.info(f"finalized_elapsed_raw_time={self.elapsed_raw_time}")
        logging.info(f"job_info={self.job_info}")
        self.output_file_name = f"result-{PROVIDER_ID}-{self.job_key}-{self.index}.tar.gz"

        if not self.run_upload():
            return False
        """
        # TODO: cloud_storage_id is list should be iterated over
        # Here we know that job is already completed
        if self.cloud_storage_id == StorageID.IPFS.value:
            self.ipfs_upload()
        if self.cloud_storage_id == StorageID.IPFS_MINILOCK.value:
            self.ipfs_minilock_upload()
        elif self.cloud_storage_id == StorageID.EUDAT.value:
            self.get_shared_tokens()
            success = self.eudat_upload()
        elif self.cloud_storage_id == StorageID.GDRIVE.value:
            self.gdrive_upload()
        """

        if not success:
            return False

        dataTransferSum = self.dataTransferIn + self.dataTransferOut
        logging.info(f"dataTransferIn={self.dataTransferIn} MB => rounded={int(self.dataTransferIn)} MB")
        logging.info(f"dataTransferOut={self.dataTransferOut} MB => rounded={int(self.dataTransferOut)} MB")
        logging.info(f"dataTransferSum={dataTransferSum} MB => rounded={int(dataTransferSum)} MB")
        bp()
        self.process_payment_tx()
        logging.info("COMPLETED")
        # TODO; garbage collector: Removed downloaded code from local since it is not needed anymore


class EudatClass(ENDCODE):
    def __init__(self, _job_key, _index, _cloud_storage_id, _received_block_number, _folder_name, _slurm_job_id,) -> None:
        super(self.__class__, self).__init__(_job_key, _index, _cloud_storage_id, _received_block_number, _folder_name, _slurm_job_id,)
        logging.info("Entered into EUDAT case")

    def run_upload(self):
        self.get_shared_tokens()
        return self.upload()

    def _upload(self, path, source_code_hash) -> bool:
        success, patch_name, patch_file = git_diff_patch(path, source_code_hash, self.index, self.results_folder_prev)
        # TODO: maybe tar the patch file
        time.sleep(0.1)
        _dataTransferOut = lib.calculate_folder_size(patch_file)
        logging.info(f"[{source_code_hash}]'s dataTransferOut => {_dataTransferOut} MB")
        self.dataTransferOut += _dataTransferOut
        success = upload_results_to_eudat(self.encoded_share_tokens[source_code_hash], patch_name, self.results_folder_prev, 5)
        if not success:
            return False

        return True


class GdriveClass(ENDCODE):
    def __init__(self, _job_key, _index, _cloud_storage_id, _received_block_number, _folder_name, _slurm_job_id,) -> None:
        super(self.__class__, self).__init__(_job_key, _index, _cloud_storage_id, _received_block_number, _folder_name, _slurm_job_id,)
        logging.info("Entered into GDRIVE case")

    def run_upload(self):
        # TODO: get other data info
        return self.upload()

    def _upload(self, path, key) -> True:
        success, patch_name, patch_file = git_diff_patch(path, key, self.index, self.results_folder_prev)

        # Stored for both pipes otherwise its read and lost
        success, gdrive_info = lib.subprocess_call_attempt(
            [GDRIVE, "info", "--bytes", key, "-c", GDRIVE_METADATA], 100, 1,
        )
        if not success:
            return False

        mime_type = get_gdrive_file_info(gdrive_info, "Mime")
        logging.info(f"mime_type={mime_type}")

        # cmd = ["tar", "-N", self.modified_date, "-jcvf", patch_file] + glob.glob("*")
        # success, output = run_command(cmd, None, True)
        # logging.info(output)
        # time.sleep(0.1)
        self.dataTransferOut = lib.calculate_folder_size(patch_file)
        logging.info(f"dataTransferOut={self.dataTransferOut} MB => rounded={int(self.dataTransferOut)} MB")
        if "folder" in mime_type:  # Received job is in folder format
            logging.info("mime_type=folder")
            cmd = [GDRIVE, "upload", "--parent", key, patch_file, "-c", GDRIVE_METADATA,]
        elif "gzip" in mime_type:  # Received job is in folder tar.gz
            logging.info("mime_type=tar.gz")
            cmd = [GDRIVE, "update", key, patch_file, "-c", GDRIVE_METADATA,]
        elif "/zip" in mime_type:  # Received job is in zip format
            logging.info("mime_type=zip")
            cmd = [GDRIVE, "update", key, patch_file, "-c", GDRIVE_METADATA,]
        else:
            logging.error("E: Files could not be uploaded")
            return False

        success, output = lib.subprocess_call_attempt(cmd, 100)
        logging.info(output)
        return success


if __name__ == "__main__":
    _job_key = sys.argv[1]
    _index = sys.argv[2]
    _cloud_storage_id = int(sys.argv[3])
    _received_block_number = sys.argv[4]
    _folder_name = sys.argv[5]
    _slurm_job_id = sys.argv[6]

    """
    if _cloud_storage_id == StorageID.IPFS.value:
        self.ipfs_upload()
    elif _cloud_storage_id == StorageID.IPFS_MINILOCK.value:
        self.ipfs_minilock_upload()
    elif _cloud_storage_id == StorageID.EUDAT.value:
        self.get_shared_tokens()
        success = self.eudat_upload()
    """
    if _cloud_storage_id == StorageID.GDRIVE.value:
        cloud_storage = GdriveClass(_job_key, _index, _cloud_storage_id, _received_block_number, _folder_name, _slurm_job_id,)

    cloud_storage.run()

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

# self.remove_source_code()
# cmd: tar -jcvf result-$providerID-$index.tar.gz *
# cmd = ['tar', '-jcvf', self.output_file_name] + glob.glob("*")
# log.write(run_command(cmd))
# cmd = ["tar", "-N", self.modified_date, "-czfj", self.output_file_name] + glob.glob("*")
# success, output = run_command(cmd, None, True)
# logging.info(f"Files to be archived using tar: \n {output}")
