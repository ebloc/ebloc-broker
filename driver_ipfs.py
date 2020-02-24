#!/usr/bin/env python3

import os
import subprocess
import time

import config
import lib
from config import logging
from lib import PROGRAM_PATH, is_ipfs_running, log, silent_remove


class IpfsClass:
    def __init__(self, loggedJob, jobInfo, requesterID, already_cached, oc):
        # cacheType is should be public on IPFS
        self.requesterID = requesterID
        self.jobInfo = jobInfo
        self.loggedJob = loggedJob
        self.requesterID = requesterID
        self.jobKey = self.loggedJob.args["jobKey"]
        self.index = self.loggedJob.args["index"]
        self.source_code_hasheses = loggedJob.args["sourceCodeHash"]
        self.cloudStorageID = loggedJob.args["cloudStorageID"]
        self.shareToken = "-1"
        # if the requested file is already cached, it stays as 0
        self.dataTransferIn = 0
        self.results_folder_prev = f"{PROGRAM_PATH}/{self.requesterID}/{self.jobKey}_{self.index}"
        self.results_folder = f"{self.results_folder_prev}/JOB_TO_RUN"

    def run(self):
        log(f"=> New job has been received. IPFS call | {time.ctime()}", "blue")
        is_ipfs_running()
        is_ipfs_hash_cached = lib.is_ipfs_hash_cached(self.jobKey)
        logging.info(f"is_ipfs_hash_cached={is_ipfs_hash_cached}")

        if not os.path.isdir(self.results_folder):
            os.makedirs(self.results_folder)

        silent_remove(f"{self.results_folder}/{self.jobKey}")

        cumulativeSize_list = []
        ipfs_hash_list = []

        status, ipfsStat, cumulativeSize = lib.is_ipfs_hash_exists(self.jobKey, attemptCount=1)
        ipfs_hash_list.append(self.jobKey)
        cumulativeSize_list.append(cumulativeSize)

        if not status or not ("CumulativeSize" in ipfsStat):
            logging.error("E: Markle not found! Timeout for the IPFS object stat retrieve")
            return False

        for source_code_hash in self.source_code_hashes:
            sourceCodeIpfsHash = lib.convertBytes32ToIpfs(source_code_hash)
            if sourceCodeIpfsHash not in ipfs_hash_list:  # jobKey as data hash already may added to the list
                status, ipfsStat, cumulativeSize = lib.is_ipfs_hash_exists(sourceCodeIpfsHash, attemptCount=1)
                cumulativeSize_list.append(cumulativeSize)
                ipfs_hash_list.append(sourceCodeIpfsHash)
                if not status:
                    return False

        initialSize = lib.calculate_folder_size(self.results_folder, "d")
        print(initialSize)

        for ipfs_hash in ipfs_hash_list:  # Here scripts knows that provided IPFS hashes exists
            logging.info(f"Attempting to get IPFS file {ipfs_hash}")
            hashedFlag = False
            if lib.is_ipfs_hash_cached(ipfs_hash):
                hashedFlag = True
                logging.info(f"IPFS file {ipfs_hash} is already cached.")

            lib.get_ipfs_hash(ipfs_hash, self.results_folder, False)
            if self.cloudStorageID == lib.StorageID.IPFS_MINILOCK.value:  # Case for the ipfsMiniLock
                with open(f"{lib.LOG_PATH}/private/miniLockPassword.txt", "r") as content_file:
                    passW = content_file.read().strip()

                # cmd: mlck decrypt -f $results_folder/$ipfsHash --passphrase="$passW" --output-file=$results_folder/output.tar.gz
                command = [
                    "mlck",
                    "decrypt",
                    "-f",
                    f"{self.results_folder}/ipfsHash",
                    f"--passphrase={passW}",
                    f"--output-file={self.results_folder}/output.tar.gz",
                ]
                passW = None
                status, res = lib.execute_shell_command(command)
                command = None
                logging.info(f"mlck decrypt status={status}")
                # cmd: tar -xvf $results_folder/output.tar.gz -C results_folder
                tar_file = f"{self.results_folder}/output.tar.gz"
                subprocess.run(["tar", "-xvf", tar_file, "-C", self.results_folder])
                silent_remove(f"{self.results_folder}/{ipfs_hash}")
                silent_remove(f"{self.results_folder}/output.tar.gz")

            if not hashedFlag:
                folderSize = lib.calculate_folder_size(self.results_folder, "d")
                self.dataTransferIn += folderSize - initialSize
                initialSize = folderSize
                # dataTransferIn += lib.convert_byte_to_mb(cumulativeSize)

            if not os.path.isfile(f"{self.results_folder}/run.sh"):
                logging.error("run.sh file does not exist")
                return False

        logging.info(f"dataTransferIn={self.dataTransferIn} MB | Rounded={int(self.dataTransferIn)} MB")

        lib.sbatchCall(
            self.loggedJob,
            self.shareToken,
            self.requesterID,
            self.results_folder,
            self.results_folder_prev,
            self.dataTransferIn,
            self.source_code_hashes,
            self.jobInfo,
        )

    """ TODO: delete
    def driverGithub(loggedJob, jobInfo, requesterID):
        import Driver
        eBlocBroker = Driver.eBlocBroker # global usage
        w3 = Driver.w3 # global usage

        globals()['jobKey']    = loggedJob.args['jobKey']
        globals()['index']     = loggedJob.args['index']
        globals()['cloudStorageID'] = loggedJob.args['cloudStorageID']

        shareToken = '-1'
        jobKeyGit = str(jobKey).replace("=", "/")
        dataTransferIn = 0 # if the requested file is already cached, it stays as 0

        results_folder_prev = lib.PROGRAM_PATH  + "/" + requesterID + "/" + jobKey + "_" + index
        results_folder     = results_folder_prev + '/JOB_TO_RUN'
        if not os.path.isdir(results_folder_prev):  # If folder does not exist
            os.makedirs(lib.PROGRAM_PATH + "/" + requesterID + "/" + jobKey + "_" + index)

        if not os.path.exists(results_folder):
            # cmd: git clone https://github.com/$jobKeyGit.git $results_folder
            subprocess.run(['git', 'clone', 'https://github.com/' + jobKeyGit + '.git', results_folder])  # Gets the source code
        else:
            pass; # TODO: maybe add git pull

        dataTransferIn = lib.calculate_folder_size(results_folder)
        lib.sbatchCall(loggedJob, shareToken, requesterID, results_folder, results_folder_prev, dataTransferIn, sourceCodeHash_list, jobInfo)
    """
