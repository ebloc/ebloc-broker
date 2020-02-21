#!/usr/bin/env python3

import os
import subprocess

import lib
from imports import connect
from lib import log, silent_remove


def calculateDataTransferOut(outputFileName):
    p1 = subprocess.Popen(["du", "-sb", outputFileName], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["awk", "{print $1}"], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    dataTransferIn = p2.communicate()[0].decode("utf-8").strip()  # Retunrs downloaded files size in bytes
    dataTransferIn = lib.convert_byte_to_mb(dataTransferIn)
    log(
        "dataTransferIn=" + str(dataTransferIn) + " MB | Rounded=" + str(int(dataTransferIn)) + " MB",
        "green",
        True,
        log_fname,
    )
    return dataTransferIn


"""
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

    resultsFolderPrev = lib.PROGRAM_PATH  + "/" + requesterID + "/" + jobKey + "_" + index
    resultsFolder     = resultsFolderPrev + '/JOB_TO_RUN'
    if not os.path.isdir(resultsFolderPrev):  # If folder does not exist
        os.makedirs(lib.PROGRAM_PATH + "/" + requesterID + "/" + jobKey + "_" + index)

    if not os.path.exists(resultsFolder):
        # cmd: git clone https://github.com/$jobKeyGit.git $resultsFolder
        subprocess.run(['git', 'clone', 'https://github.com/' + jobKeyGit + '.git', resultsFolder])  # Gets the source code
    else:
        pass; # TODO: maybe add git pull

    dataTransferIn = calculateDataTransferOut(resultsFolder)
    lib.sbatchCall(loggedJob, shareToken, requesterID, resultsFolder, resultsFolderPrev, dataTransferIn, sourceCodeHash_list, jobInfo)
"""


def driverIpfs(loggedJob, jobInfo, requesterID):
    import Driver

    eBlocBroker, w3 = connect()

    globals()["jobKey"] = loggedJob.args["jobKey"]
    globals()["index"] = loggedJob.args["index"]
    globals()["cloudStorageID"] = loggedJob.args["cloudStorageID"]
    globals()["sourceCodeHashes"] = loggedJob.args["sourceCodeHash"]
    globals()["log_fname"] = lib.LOG_PATH + "/transactions/" + jobKey + "_" + str(index) + "_driverOutput" + ".txt"
    # cacheType is should be public on IPFS

    shareToken = "-1"

    lib.isIpfsOn()
    log("jobKey=" + jobKey, "", True, log_fname)
    isIpfsHashCached = lib.isIpfsHashCached(jobKey)
    log("isIpfsHashCached=" + str(isIpfsHashCached), "", True, log_fname)

    dataTransferIn = 0  # if the requested file is already cached, it stays as 0
    resultsFolderPrev = lib.PROGRAM_PATH + "/" + requesterID + "/" + jobKey + "_" + str(index)
    resultsFolder = resultsFolderPrev + "/JOB_TO_RUN"

    if not os.path.isdir(resultsFolderPrev):  # If folder does not exist
        os.makedirs(resultsFolderPrev, exist_ok=True)
        os.makedirs(resultsFolder, exist_ok=True)

    if os.path.isfile(resultsFolder + "/" + jobKey):
        silent_remove(resultsFolder + "/" + jobKey)

    cumulativeSize_list = []
    sourceCodeHash_list = []
    ipfsHash_list = []

    status, ipfsStat, cumulativeSize = lib.isIpfsHashExists(jobKey, attemptCount=1)
    ipfsHash_list.append(jobKey)
    cumulativeSize_list.append(cumulativeSize)

    if not status or not ("CumulativeSize" in ipfsStat):
        log("E: Markle not found! Timeout for the IPFS object stat retrieve", "red", True, log_fname)
        return False

    for i in range(0, len(globals()["sourceCodeHashes"])):
        sourceCodeHash = globals()["sourceCodeHashes"][i]
        sourceCodeHash_list.append(sourceCodeHash)
        sourceCodeIpfsHash = lib.convertBytes32ToIpfs(sourceCodeHash)
        if sourceCodeIpfsHash not in ipfsHash_list:  # jobKey as data hash already may added to the list
            status, ipfsStat, cumulativeSize = lib.isIpfsHashExists(sourceCodeIpfsHash, attemptCount=1)
            cumulativeSize_list.append(cumulativeSize)
            ipfsHash_list.append(sourceCodeIpfsHash)
            if not status:
                return False

    dataTransferIn = 0
    initialSize = lib.calculateFolderSize(resultsFolder, "d")
    print(initialSize)
    for i in range(0, len(ipfsHash_list)):  # Here scripts knows that provided IPFS hashes exists
        ipfsHash = ipfsHash_list[i]
        log('Attempting to get IPFS file "' + ipfsHash + '"', "light_sea_green", True, log_fname)
        print(ipfsHash_list[i])
        hashedFlag = False
        if lib.isIpfsHashCached(ipfsHash):
            hashedFlag = True
            log('IPFS file "' + ipfsHash + '" is already cached.', "green", True, log_fname)

        lib.getIpfsHash(ipfsHash, resultsFolder, false)
        if cloudStorageID == lib.StorageID.IPFS_MINILOCK.value:  # Case for the ipfsMiniLock
            with open(lib.LOG_PATH + "/private/miniLockPassword.txt", "r") as content_file:
                passW = content_file.read().strip()

            # cmd: mlck decrypt -f $resultsFolder/$ipfsHash --passphrase="$passW" --output-file=$resultsFolder/output.tar.gz
            command = [
                "mlck",
                "decrypt",
                "-f",
                resultsFolder + "/" + ipfsHash,
                "--passphrase=" + passW,
                "--output-file=" + resultsFolder + "/output.tar.gz",
            ]
            passW = None
            status, res = lib.execute_shell_command(command)
            log("mlck decrypt status=" + str(status), "", True, log_fname)
            # cmd: tar -xvf $resultsFolder/output.tar.gz -C resultsFolder
            subprocess.run(["tar", "-xvf", resultsFolder + "/output.tar.gz", "-C", resultsFolder])
            silent_remove(resultsFolder + "/" + ipfsHash)
            silent_remove(resultsFolder + "/output.tar.gz")

        if not hashedFlag:
            folderSize = lib.calculateFolderSize(resultsFolder, "d")
            dataTransferIn += folderSize - initialSize
            initialSize = folderSize
            # dataTransferIn += lib.convert_byte_to_mb(cumulativeSize)

        if not os.path.isfile(resultsFolder + "/run.sh"):
            log("run.sh does not exist", "red", True, log_fname)
            return False

    log(
        "dataTransferIn=" + str(dataTransferIn) + " MB | Rounded=" + str(int(dataTransferIn)) + " MB",
        "green",
        True,
        log_fname,
    )
    lib.sbatchCall(
        loggedJob,
        shareToken,
        requesterID,
        resultsFolder,
        resultsFolderPrev,
        dataTransferIn,
        sourceCodeHash_list,
        jobInfo,
    )
