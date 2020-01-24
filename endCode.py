#!/usr/bin/env python3

import sys
import os
import time
import lib
import base64
import glob
import getpass
import subprocess
import json
import hashlib

from colored import stylize
from colored import fg
from os.path import expanduser

from lib import executeShellCommand, PROVIDER_ID
from imports import connectEblocBroker, getWeb3
from contractCalls.get_job_info import getJobSourceCodeHash, get_job_info
from contractCalls.get_requester_info import get_requester_info
from contractCalls.processPayment import processPayment

w3 = getWeb3()
eBlocBroker = connectEblocBroker(w3)
homeDir = expanduser("~")


def log(strIn, color=""):
    if color != "":
        print(stylize(strIn, fg(color)))
    else:
        print(strIn)
        logFileName = lib.LOG_PATH + "/endCodeAnalyse/" + globals()["jobKey"] + "_" + globals()["index"] + ".txt"
        txFile = open(logFileName, "a")
        txFile.write(strIn + "\n")
        txFile.close()


def uploadResultToEudat(encodedShareToken, outputFileName):
    """ cmd: ( https://stackoverflow.com/a/44556541/2402577, https://stackoverflow.com/a/24972004/2402577 )
    curl -X PUT -H \'Content-Type: text/plain\' -H \'Authorization: Basic \'$encodedShareToken\'==\' \
            --data-binary \'@result-\'$providerID\'-\'$index\'.tar.gz\' https://b2drop.eudat.eu/public.php/webdav/result-$providerID-$index.tar.gz

    curl --fail -X PUT -H 'Content-Type: text/plain' -H 'Authorization: Basic 'SjQzd05XM2NNcFoybkFLOg'==' --data-binary
    '@0b2fe6dd7d8e080e84f1aa14ad4c9a0f_0.txt' https://b2drop.eudat.eu/public.php/webdav/result.txt
    """
    p = subprocess.Popen(
        [
            "curl",
            "--fail",
            "-X",
            "PUT",
            "-H",
            "Content-Type: text/plain",
            "-H",
            "Authorization: Basic " + encodedShareToken,
            "--data-binary",
            "@" + outputFileName,
            "https://b2drop.eudat.eu/public.php/webdav/" + outputFileName,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    output, err = p.communicate()
    return p, output, err


def processPaymentTx(
    jobKey,
    index,
    jobID,
    elapsedRawTime,
    resultIpfsHash,
    cloudStorageID,
    slurmJobID,
    dataTransfer,
    sourceCodeHashArray,
    jobInfo,
):
    # cmd: scontrol show job slurmJobID | grep 'EndTime'| grep -o -P '(?<=EndTime=).*(?= )'
    status, output = executeShellCommand(["scontrol", "show", "job", slurmJobID], None, True)
    p1 = subprocess.Popen(["echo", output], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["grep", "EndTime"], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    p3 = subprocess.Popen(["grep", "-o", "-P", "(?<=EndTime=).*(?= )"], stdin=p2.stdout, stdout=subprocess.PIPE)
    p2.stdout.close()
    date = p3.communicate()[0].decode("utf-8").strip()

    command = ["date", "-d", date, "+'%s'"]  # cmd: date -d 2018-09-09T21:50:51 +"%s"
    status, endTimeStamp = executeShellCommand(command, None, True)
    endTimeStamp = endTimeStamp.replace("'", "")
    log("endTimeStamp=" + endTimeStamp)

    status, tx_hash = lib.eBlocBrokerFunctionCall(
        lambda: processPayment(
            jobKey,
            index,
            jobID,
            elapsedRawTime,
            resultIpfsHash,
            cloudStorageID,
            endTimeStamp,
            dataTransfer,
            sourceCodeHashArray,
            jobInfo["core"],
            jobInfo["executionDuration"],
            eBlocBroker,
            w3,
        ),
        10,
    )
    if not status:
        sys.exit()

    log("processPayment()_tx_hash=" + tx_hash)
    txFile = open(lib.LOG_PATH + "/transactions/" + PROVIDER_ID + ".txt", "a")
    txFile.write(jobKey + "_" + index + "| Tx_hash: " + tx_hash + "| processPaymentTxHash\n")
    txFile.close()


# Client's loaded files are removed, no need to re-upload them.
def removeSourceCode(resultsFolderPrev, resultsFolder):
    # cmd: find . -type f ! -newer $resultsFolder/timestamp.txt  # Client's loaded files are removed, no need to re-upload them.
    command = ["find", resultsFolder, "-type", "f", "!", "-newer", resultsFolderPrev + "/timestamp.txt"]
    status, filesToRemove = executeShellCommand(command, None, True)
    if filesToRemove != "" or filesToRemove is not None:
        log("\nFiles to be removed: \n" + filesToRemove + "\n")
    # cmd: find . -type f ! -newer $resultsFolder/timestamp.txt -delete
    subprocess.run(
        ["find", resultsFolder, "-type", "f", "!", "-newer", resultsFolderPrev + "/timestamp.txt", "-delete"]
    )


# cloudStorageID: string
def endCall(jobKey, index, cloudStorageID, shareToken, folderName, slurmJobID):
    globals()["jobKey"] = jobKey
    globals()["index"] = index
    jobID = 0  # TODO: should be mapped slurmJobID

    # https://stackoverflow.com/a/5971326/2402577 ... https://stackoverflow.com/a/4453495/2402577
    # my_env = os.environ.copy();
    # my_env["IPFS_PATH"] = homeDir + "/.ipfs"
    # print(my_env)
    os.environ["IPFS_PATH"] = homeDir + "/.ipfs"

    log("To run again:")
    log(
        "~/eBlocBroker/endCode.py "
        + jobKey
        + " "
        + index
        + " "
        + cloudStorageID
        + " "
        + shareToken
        + " "
        + folderName
        + " "
        + slurmJobID
        + "\n"
    )
    log("slurmJobID=" + slurmJobID)
    if jobKey == index:
        log("JobKey and index are same.", "red")
        sys.exit()

    encodedShareToken = ""
    if shareToken != "-1":
        encodedShareToken = base64.b64encode((str(shareToken) + ":").encode("utf-8")).decode("utf-8")

    log("encodedShareToken: " + encodedShareToken)
    log("./get_job_info.py " + " " + PROVIDER_ID + " " + jobKey + " " + index + " " + str(jobID))

    try:
        job, received, jobOwner, dataTransferIn, dataTransferOut = eBlocBroker.functions.getJobInfo(
            w3.toChecksumAddress(PROVIDER_ID), jobKey, int(index), int(jobID)
        ).call()
    except Exception:
        import traceback

        log(traceback.format_exc(), "red")
        sys.exit()

    requesterID = jobOwner.lower()
    requesterIDAddr = hashlib.md5(requesterID.encode("utf-8")).hexdigest()  # Convert Ethereum User Address into 32-bits
    status, requesterInfo = get_requester_info(requesterID, eBlocBroker, w3)

    resultsFolderPrev = lib.PROGRAM_PATH + "/" + requesterIDAddr + "/" + jobKey + "_" + index
    resultsFolder = resultsFolderPrev + "/JOB_TO_RUN"

    file_name = "receivedBlockNumber.txt"
    if os.path.isfile(resultsFolderPrev + "/" + file_name):
        _file = open(resultsFolderPrev + "/" + file_name, "r")
        receivedBlockNumber = _file.read().rstrip("\n")
        _file.close()
        log("receivedBlockNumber=" + receivedBlockNumber)

    status, jobInfo = lib.eBlocBrokerFunctionCall(
        lambda: get_job_info(PROVIDER_ID, jobKey, index, jobID, receivedBlockNumber, eBlocBroker, w3), 10
    )
    if not status:
        sys.exit()

    # cmd: find ./ -size 0 -print0 | xargs -0 rm
    p1 = subprocess.Popen(["find", resultsFolder, "-size", "0", "-print0"], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["xargs", "-0", "-r", "rm"], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    p2.communicate()  # Remove empty files if exist

    # cmd: find ./ -type d -empty -delete | xargs -0 rmdir
    subprocess.run(["find", resultsFolder, "-type", "d", "-empty", "-delete"])
    p1 = subprocess.Popen(["find", resultsFolder, "-type", "d", "-empty", "-print0"], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["xargs", "-0", "-r", "rmdir"], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    p2.communicate()  # Remove empty folders if exist

    log("\nwhoami: " + getpass.getuser() + " " + str(os.getegid()))  # whoami
    log("homeDir: " + homeDir)  # $HOME
    log("pwd: " + os.getcwd())  # pwd
    log("resultsFolder: " + resultsFolder)
    log("jobKey: " + jobKey)
    log("index: " + index)
    log("cloudStorageID: " + cloudStorageID)
    log("shareToken: " + shareToken)
    log("encodedShareToken: " + encodedShareToken)
    log("folderName: " + folderName)
    log("providerID: " + PROVIDER_ID)
    log("requesterIDAddr: " + requesterIDAddr)
    log("received: " + str(jobInfo["received"]))

    dataTransferIn = 0
    if os.path.isfile(resultsFolderPrev + "/dataTransferIn.txt"):
        with open(resultsFolderPrev + "/dataTransferIn.txt") as json_file:
            data = json.load(json_file)
            dataTransferIn = data["dataTransferIn"]
    else:
        log("dataTransferIn.txt does not exist...", "red")

    log("dataTransferIn=" + str(dataTransferIn) + " MB | Rounded=" + str(int(dataTransferIn)) + " MB", "green")
    file_name = "modifiedDate.txt"
    if os.path.isfile(resultsFolderPrev + "/" + file_name):
        _file = open(resultsFolderPrev + "/" + file_name, "r")
        modifiedDate = _file.read().rstrip("\n")
        _file.close()
        log("modifiedDate=" + modifiedDate)

    miniLockID = requesterInfo["miniLockID"]
    log("\njobOwner's Info: ")
    log("{0: <12}".format("email:") + requesterInfo["email"])
    log("{0: <12}".format("miniLockID:") + miniLockID)
    log("{0: <12}".format("ipfsID:") + requesterInfo["ipfsID"])
    log("{0: <12}".format("fID:") + requesterInfo["fID"])
    log("")

    if jobInfo["jobStateCode"] == str(lib.job_state_code["COMPLETED"]):
        log("Job is completed and already get paid.", "red")
        sys.exit()

    executionDuration = jobInfo["executionDuration"]
    log("requesterExecutionTime: " + str(executionDuration[jobID]) + " minutes")  # Clients minuteGas for the job
    count = 0
    while True:
        if count > 10:
            sys.exit()

        count += 1
        if (
            jobInfo["jobStateCode"] == lib.job_state_code["RUNNING"]
        ):  # It will come here eventually, when setJob() is deployed.
            log("Job has been started.", "green")
            break  # Wait until does values updated on the blockchain

        if jobInfo["jobStateCode"] == lib.job_state_code["COMPLETED"]:
            log("E: Job is already completed job and its money is received.", "red")
            sys.exit()  # Detects an error on the SLURM side

        status, jobInfo = lib.eBlocBrokerFunctionCall(
            lambda: get_job_info(PROVIDER_ID, jobKey, index, jobID, receivedBlockNumber, eBlocBroker, w3), 10
        )
        if not status:
            sys.exit()

        log("Waiting for " + str(count * 15) + " seconds to pass...", "yellow")
        time.sleep(15)  # Short sleep here so this loop is not keeping CPU busy //setJobStatus may deploy late.

    # sourceCodeHashes of the completed job is obtained from its logged event
    status, jobInfo = lib.eBlocBrokerFunctionCall(
        lambda: getJobSourceCodeHash(jobInfo, PROVIDER_ID, jobKey, index, jobID, receivedBlockNumber, eBlocBroker, w3),
        10,
    )
    if not status:
        sys.exit()

    log("jobName=" + str(folderName))
    with open(resultsFolder + "/slurmJobInfo.out", "w") as stdout:
        command = [
            "scontrol",
            "show",
            "job",
            slurmJobID,
        ]  # cmd: scontrol show job $slurmJobID > $resultsFolder/slurmJobInfo.out
        subprocess.Popen(command, stdout=stdout)
        log("Writing into slurmJobInfo.out file is completed", "green")

    command = [
        "sacct",
        "-n",
        "-X",
        "-j",
        slurmJobID,
        "--format=Elapsed",
    ]  # cmd: sacct -n -X -j $slurmJobID --format="Elapsed"
    status, elapsedTime = executeShellCommand(command, None, True)
    log("ElapsedTime=" + elapsedTime)

    elapsedTime = elapsedTime.split(":")
    elapsedDay = "0"
    elapsedHour = elapsedTime[0].replace(" ", "")
    elapsedMinute = elapsedTime[1].rstrip()

    if "-" in str(elapsedHour):
        elapsedHour = elapsedHour.split("-")
        elapsedDay = elapsedHour[0]
        elapsedHour = elapsedHour[1]

    elapsedRawTime = int(elapsedDay) * 1440 + int(elapsedHour) * 60 + int(elapsedMinute) + 1
    log("ElapsedRawTime=" + str(elapsedRawTime))

    if elapsedRawTime > int(executionDuration[jobID]):
        elapsedRawTime = executionDuration[jobID]

    log("finalizedElapsedRawTime: " + str(elapsedRawTime))
    log("jobInfo: " + str(jobInfo))
    outputFileName = "result-" + PROVIDER_ID + "-" + jobKey + "-" + str(index) + ".tar.gz"

    # Here we know that job is already completed
    if cloudStorageID == str(lib.StorageID.IPFS.value) or cloudStorageID == str(lib.StorageID.GITHUB.value):
        removeSourceCode(resultsFolderPrev, resultsFolder)
        for attempt in range(10):
            command = ["ipfs", "add", "-r", resultsFolder]  # Uploaded as folder
            status, resultIpfsHash = executeShellCommand(command, None, True)
            if not status or resultIpfsHash == "":
                """ Approach to upload as .tar.gz. Currently not used.
                removeSourceCode(resultsFolderPrev)
                with open(resultsFolderPrev + '/modifiedDate.txt') as content_file:
                date = content_file.read().strip()
                command = ['tar', '-N', date, '-jcvf', outputFileName] + glob.glob("*")
                log(executeShellCommand(command, None, True))
                command = ['ipfs', 'add', resultsFolder + '/result.tar.gz']
                status, resultIpfsHash = executeShellCommand(command)
                resultIpfsHash = resultIpfsHash.split(' ')[1]
                silentremove(resultsFolder + '/result.tar.gz')
                """
                log("Generated new hash return empty error. Trying again... Try count: " + str(attempt), "yellow")
                time.sleep(5)  # wait 5 second for next step retry to up-try
            else:  # success
                break
        else:  # we failed all the attempts - abort
            sys.exit()

        # dataTransferOut = lib.calculateFolderSize(resultsFolder, 'd')
        # log('dataTransferOut=' + str(dataTransferOut) + ' MB | Rounded=' + str(int(dataTransferOut)) + ' MB', 'green')
        resultIpfsHash = lib.getIpfsParentHash(resultIpfsHash)
        command = ["ipfs", "pin", "add", resultIpfsHash]
        status, res = executeShellCommand(command, None, True)  # pin downloaded ipfs hash
        print(res)

        command = ["ipfs", "object", "stat", resultIpfsHash]
        status, isIPFSHashExist = executeShellCommand(command, None, True)  # pin downloaded ipfs hash
        for item in isIPFSHashExist.split("\n"):
            if "CumulativeSize" in item:
                dataTransferOut = item.strip().split()[1]
                break

        dataTransferOut = lib.convertByteToMB(dataTransferOut)
        log("dataTransferOut=" + str(dataTransferOut) + " MB | Rounded=" + str(int(dataTransferOut)) + " MB", "green")
    if cloudStorageID == str(lib.StorageID.IPFS_MINILOCK.value):
        os.chdir(resultsFolder)
        with open(resultsFolderPrev + "/modifiedDate.txt") as content_file:
            date = content_file.read().strip()

        command = ["tar", "-N", date, "-jcvf", outputFileName] + glob.glob("*")
        status, result = executeShellCommand(command, None, True)
        log(result)
        # cmd: mlck encrypt -f $resultsFolder/result.tar.gz $miniLockID --anonymous --output-file=$resultsFolder/result.tar.gz.minilock
        command = [
            "mlck",
            "encrypt",
            "-f",
            resultsFolder + "/result.tar.gz",
            miniLockID,
            "--anonymous",
            "--output-file=" + resultsFolder + "/result.tar.gz.minilock",
        ]
        status, res = executeShellCommand(command, None, True)
        log(res)
        removeSourceCode(resultsFolderPrev, resultsFolder)
        for attempt in range(10):
            command = ["ipfs", "add", resultsFolder + "/result.tar.gz.minilock"]
            status, resultIpfsHash = executeShellCommand(command, None, True)
            resultIpfsHash = resultIpfsHash.split(" ")[1]
            if resultIpfsHash == "":
                log("Generated new hash return empty error. Trying again... Try count: " + str(attempt), "yellow")
                time.sleep(5)  # wait 5 second for next step retry to up-try
            else:  # success
                break
        else:  # we failed all the attempts - abort
            sys.exit()

        # dataTransferOut = lib.calculateFolderSize(resultsFolder + '/result.tar.gz.minilock', 'f')
        # log('dataTransferOut=' + str(dataTransferOut) + ' MB | Rounded=' + str(int(dataTransferOut)) + ' MB', 'green')
        log("resultIpfsHash: " + resultIpfsHash)
        command = ["ipfs", "pin", "add", resultIpfsHash]
        status, res = executeShellCommand(command, None, True)
        print(res)
        command = ["ipfs", "object", "stat", resultIpfsHash]
        status, isIPFSHashExist = executeShellCommand(command, None, True)
        for item in isIPFSHashExist.split("\n"):
            if "CumulativeSize" in item:
                dataTransferOut = item.strip().split()[1]
                break

        dataTransferOut = lib.convertByteToMB(dataTransferOut)
        log("dataTransferOut=" + str(dataTransferOut) + " MB | Rounded=" + str(int(dataTransferOut)) + " MB", "green")
    elif cloudStorageID == str(lib.StorageID.EUDAT.value):
        log("Entered into Eudat case")
        resultIpfsHash = ""
        lib.removeFiles(resultsFolder + "/.node-xmlhttprequest*")
        os.chdir(resultsFolder)
        removeSourceCode(resultsFolderPrev, resultsFolder)
        # cmd: tar -jcvf result-$providerID-$index.tar.gz *
        # command = ['tar', '-jcvf', outputFileName] + glob.glob("*")
        # log(executeShellCommand(command))
        with open(resultsFolderPrev + "/modifiedDate.txt") as content_file:
            date = content_file.read().strip()

        command = ["tar", "-N", date, "-jcvf", outputFileName] + glob.glob("*")
        status, result = executeShellCommand(command, None, True)
        log("Files to be archived using tar: \n" + result)
        dataTransferOut = lib.calculateFolderSize(outputFileName, "f")
        log("dataTransferOut=" + str(dataTransferOut) + " MB | Rounded=" + str(int(dataTransferOut)) + " MB", "green")
        for attempt in range(5):
            p, output, err = uploadResultToEudat(encodedShareToken, outputFileName)
            output = output.strip().decode("utf-8")
            err = err.decode("utf-8")
            if p.returncode != 0 or "<d:error" in output:
                log("E: EUDAT repository did not successfully loaded.", "red")
                log("curl failed %d %s . %s" % (p.returncode, err.decode("utf-8"), output))
                time.sleep(1)  # wait 1 second for next step retry to upload
            else:  # success on upload
                break
        else:  # we failed all the attempts - abort
            sys.exit()
    elif cloudStorageID == str(lib.StorageID.GDRIVE.value):
        resultIpfsHash = ""
        # cmd: gdrive info $jobKey -c $GDRIVE_METADATA # stored for both pipes otherwise its read and lost
        status, gdriveInfo = lib.subprocessCallAttempt(
            [lib.GDRIVE, "info", "--bytes", jobKey, "-c", lib.GDRIVE_METADATA], 500, 1
        )
        if not status:
            return False

        mimeType = lib.getGdriveFileInfo(gdriveInfo, "Mime")
        log("mimeType=" + str(mimeType))
        os.chdir(resultsFolder)
        # if 'folder' in mimeType:  # Received job is in folder format
        removeSourceCode(resultsFolderPrev, resultsFolder)
        with open(resultsFolderPrev + "/modifiedDate.txt", "r") as content_file:
            date = content_file.read().rstrip()

        command = ["tar", "-N", date, "-jcvf", outputFileName] + glob.glob("*")
        status, result = executeShellCommand(command, None, True)
        log(result)
        time.sleep(0.25)
        dataTransferOut = lib.calculateFolderSize(outputFileName, "f")
        log("dataTransferOut=" + str(dataTransferOut) + " MB | Rounded=" + str(int(dataTransferOut)) + " MB", "green")
        if "folder" in mimeType:  # Received job is in folder format
            log("mimeType=folder")
            # cmd: $GDRIVE upload --parent $jobKey result-$providerID-$index.tar.gz -c $GDRIVE_METADATA
            command = [lib.GDRIVE, "upload", "--parent", jobKey, outputFileName, "-c", lib.GDRIVE_METADATA]
            status, res = lib.subprocessCallAttempt(command, 500)
            log(res)
        elif "gzip" in mimeType:  # Received job is in folder tar.gz
            log("mimeType=tar.gz")
            # cmd: $GDRIVE update $jobKey result-$providerID-$index.tar.gz -c $GDRIVE_METADATA
            command = [lib.GDRIVE, "update", jobKey, outputFileName, "-c", lib.GDRIVE_METADATA]
            status, res = lib.subprocessCallAttempt(command, 500)
            log(res)
        elif "/zip" in mimeType:  # Received job is in zip format
            log("mimeType=zip")
            # cmd: $GDRIVE update $jobKey result-$providerID-$index.tar.gz -c $GDRIVE_METADATA
            command = [lib.GDRIVE, "update", jobKey, outputFileName, "-c", lib.GDRIVE_METADATA]
            status, res = lib.subprocessCallAttempt(command, 500)
            log(res)
        else:
            log("E: Files could not be uploaded", "red")
            sys.exit()

    dataTransferSum = dataTransferIn + dataTransferOut
    log("dataTransferIn=" + str(dataTransferIn) + " MB | Rounded=" + str(int(dataTransferIn)) + " MB", "green")
    log("dataTransferOut=" + str(dataTransferOut) + " MB | Rounded=" + str(int(dataTransferOut)) + " MB", "green")
    log("dataTransferSum=" + str(dataTransferSum) + " MB | Rounded=" + str(int(dataTransferSum)) + " MB", "green")
    processPaymentTx(
        jobKey,
        index,
        jobID,
        elapsedRawTime,
        resultIpfsHash,
        cloudStorageID,
        slurmJobID,
        int(dataTransferIn),
        int(dataTransferOut),
        jobInfo,
    )

    log("=====COMPLETED=====", "green")
    """
    # Removed downloaded code from local since it is not needed anymore
    if os.path.isdir(resultsFolderPrev):
    shutil.rmtree(resultsFolderPrev)  # deletes a directory and all its contents.
    """


if __name__ == "__main__":
    key = sys.argv[1]
    index = sys.argv[2]
    cloudStorageID = sys.argv[3]
    shareToken = sys.argv[4]
    folderName = sys.argv[5]
    slurmJobID = sys.argv[6]
    endCall(key, index, cloudStorageID, shareToken, folderName, slurmJobID)
