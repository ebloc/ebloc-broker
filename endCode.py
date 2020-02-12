#!/usr/bin/env python3

import base64
import getpass
import glob
import hashlib
import json
import os
import subprocess
import sys
import time
from os.path import expanduser

import lib
from config import logging
from contractCalls.get_job_info import get_job_info, getJobSourceCodeHash
from contractCalls.get_requester_info import get_requester_info
from contractCalls.processPayment import processPayment
from imports import connect
from lib import PROVIDER_ID, execute_shell_command

eBlocBroker, w3 = connect()
home_dir = expanduser("~")


def upload_results_to_eudat(encodedShareToken, output_file_name):
    """ cmd: ( https://stackoverflow.com/a/44556541/2402577, https://stackoverflow.com/a/24972004/2402577 )
    curl -X PUT -H \'Content-Type: text/plain\' -H \'Authorization: Basic \'$encodedShareToken\'==\' \
            --data-binary \'@result-\'$providerID\'-\'$index\'.tar.gz\' https://b2drop.eudat.eu/public.php/webdav/result-$providerID-$index.tar.gz

    curl --fail -X PUT -H 'Content-Type: text/plain' -H 'Authorization: Basic 'SjQzd05XM2NNcFoybk.Write'==' --data-binary
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
            f"Authorization: Basic {encodedShareToken}",
            "--data-binary",
            f"@{output_file_name}",
            f"https://b2drop.eudat.eu/public.php/webdav/{output_file_name}",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    output, err = p.communicate()
    return p, output, err


def process_payment_tx(
    job_key,
    index,
    jobID,
    elapsedRawTime,
    result_ipfs_hash,
    cloudStorageID,
    slurmJobID,
    dataTransfer,
    sourceCodeHashArray,
    jobInfo,
):
    # cmd: scontrol show job slurmJobID | grep 'EndTime'| grep -o -P '(?<=EndTime=).*(?= )'
    is_status, output = execute_shell_command(["scontrol", "show", "job", slurmJobID], None, True)
    p1 = subprocess.Popen(["echo", output], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["grep", "EndTime"], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    p3 = subprocess.Popen(["grep", "-o", "-P", "(?<=EndTime=).*(?= )"], stdin=p2.stdout, stdout=subprocess.PIPE)
    p2.stdout.close()
    date = p3.communicate()[0].decode("utf-8").strip()

    command = ["date", "-d", date, "+'%s'"]  # cmd: date -d 2018-09-09T21:50:51 +"%s"
    is_status, end_time_stamp = execute_shell_command(command, None, True)
    end_time_stamp = end_time_stamp.replace("'", "")
    logging.info(f"end_time_stamp={end_time_stamp}")

    is_status, tx_hash = lib.eBlocBrokerFunctionCall(
        lambda: processPayment(
            job_key,
            index,
            jobID,
            elapsedRawTime,
            result_ipfs_hash,
            cloudStorageID,
            end_time_stamp,
            dataTransfer,
            sourceCodeHashArray,
            jobInfo["core"],
            jobInfo["executionDuration"],
        ),
        10,
    )
    if not is_status:
        sys.exit()

    logging.info(f"processPayment()_tx_hash={tx_hash}")
    txFile = open(f"{lib.LOG_PATH}/transactions/{PROVIDER_ID}.txt", "a")
    txFile.write(f"{job_key}_{index} | Tx_hash: {tx_hash} | processPayment_tx_hash")
    txFile.close()


# Client's loaded files are removed, no need to re-upload them.
def removeSourceCode(results_folder_prev, results_folder):
    # cmd: find . -type f ! -newer $results_folder/timestamp.txt  # Client's loaded files are removed, no need to re-upload them.
    command = ["find", results_folder, "-type", "f", "!", "-newer", f"{results_folder_prev}/timestamp.txt"]
    is_status, files_to_remove = execute_shell_command(command, None, True)
    if files_to_remove != "" or files_to_remove is not None:
        logging.info(f"\nFiles to be removed: \n{files_to_remove}\n")
    # cmd: find . -type f ! -newer $results_folder/timestamp.txt -delete

    subprocess.run(
        ["find", results_folder, "-type", "f", "!", "-newer", f"{results_folder_prev}/timestamp.txt", "-delete"]
    )


def end_code(job_key, index, cloudStorageID, shareToken, received_block_number, folder_name, slurmJobID):
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
        handlers=[logging.FileHandler(f"{lib.LOG_PATH}/endCodeAnalyse/{job_key}_{index}.log"), logging.StreamHandler()],
    )
    logging.info("")

    jobID = 0  # TODO: should be mapped slurmJobID

    # https://stackoverflow.com/a/5971326/2402577 ... https://stackoverflow.com/a/4453495/2402577
    # my_env = os.environ.copy();
    # my_env["IPFS_PATH"] = home_dir + "/.ipfs"
    # print(my_env)
    os.environ["IPFS_PATH"] = f"{home_dir}/.ipfs"

    logging.info(
        f"~/eBlocBroker/endCode.py {job_key} {index} {cloudStorageID} {shareToken} {received_block_number} {folder_name} {slurmJobID}"
    )
    logging.info(f"slurmJobID={slurmJobID}")
    if job_key == index:
        logging.error("job_key and index are same.")
        sys.exit()

    encodedShareToken = ""
    if shareToken != "-1":
        _share_token = f"{shareToken}:"
        encodedShareToken = base64.b64encode((_share_token).encode("utf-8")).decode("utf-8")

    logging.info(f"encodedShareToken: {encodedShareToken}")
    logging.info(f"./get_job_info.py {PROVIDER_ID} {job_key} {index} {jobID}")
    is_status, jobInfo = lib.eBlocBrokerFunctionCall(
        lambda: get_job_info(PROVIDER_ID, job_key, index, jobID, received_block_number), 10
    )

    if not is_status:
        sys.exit()

    requesterID = jobInfo["jobOwner"].lower()
    requesterIDAddr = hashlib.md5(requesterID.encode("utf-8")).hexdigest()  # Convert Ethereum User Address into 32-bits
    is_status, requesterInfo = get_requester_info(requesterID)
    results_folder_prev = f"{lib.PROGRAM_PATH}/{requesterIDAddr}/{job_key}_{index}"
    results_folder = f"{results_folder_prev}/JOB_TO_RUN"

    # cmd: find ./ -size 0 -print0 | xargs -0 rm
    p1 = subprocess.Popen(["find", results_folder, "-size", "0", "-print0"], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["xargs", "-0", "-r", "rm"], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    p2.communicate()  # Remove empty files if exist

    # cmd: find ./ -type d -empty -delete | xargs -0 rmdir
    subprocess.run(["find", results_folder, "-type", "d", "-empty", "-delete"])
    p1 = subprocess.Popen(["find", results_folder, "-type", "d", "-empty", "-print0"], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["xargs", "-0", "-r", "rmdir"], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    p2.communicate()  # Remove empty folders if exist

    logging.info(f"whoami: {getpass.getuser()} os.getegid()")
    logging.info(f"home_dir: {home_dir}")
    logging.info(f"pwd: {os.getcwd()}")
    logging.info(f"results_folder: {results_folder}")
    logging.info(f"job_key: {job_key}")
    logging.info(f"index: {index}")
    logging.info(f"cloudStorageID: {cloudStorageID}")
    logging.info(f"shareToken: {shareToken}")
    logging.info(f"encodedShareToken: {encodedShareToken}")
    logging.info(f"folder_name: {folder_name}")
    logging.info(f"providerID: {PROVIDER_ID}")
    logging.info(f"requesterIDAddr: {requesterIDAddr}")
    logging.info(f"received: {jobInfo['received']}")

    dataTransferIn = 0
    if os.path.isfile(f"{results_folder_prev}/dataTransferIn.txt"):
        with open(f"{results_folder_prev}/dataTransferIn.txt") as json_file:
            data = json.load(json_file)
            dataTransferIn = data["dataTransferIn"]
    else:
        logging.error("dataTransferIn.txt does not exist...")

    logging.info(f"dataTransferIn={dataTransferIn} MB | Rounded={int(dataTransferIn)} MB")
    file_name = "modifiedDate.txt"
    if os.path.isfile(f"{results_folder_prev}/{file_name}"):
        _file = open(f"{results_folder_prev}/{file_name}", "r")
        modifiedDate = _file.read().rstrip("\n")
        _file.close()
        logging.info(f"modifiedDate={modifiedDate}")

    miniLockID = requesterInfo["miniLockID"]
    logging.info("jobOwner's Info: ")
    logging.info("{0: <12}".format("email:") + requesterInfo["email"])
    logging.info("{0: <12}".format("miniLockID:") + miniLockID)
    logging.info("{0: <12}".format("ipfsID:") + requesterInfo["ipfsID"])
    logging.info("{0: <12}".format("fID:") + requesterInfo["fID"])
    logging.info("")

    if jobInfo["jobStateCode"] == str(lib.job_state_code["COMPLETED"]):
        logging.error("Job is completed and already get paid.")
        sys.exit()

    executionDuration = jobInfo["executionDuration"]
    logging.info(f"requesterExecutionTime={executionDuration[jobID]} minutes")
    count = 0
    while True:
        if count > 10:
            sys.exit()

        count += 1
        if (
            jobInfo["jobStateCode"] == lib.job_state_code["RUNNING"]
        ):  # It will come here eventually, when setJob() is deployed.
            logging.info("Job has been started.")
            break  # Wait until does values updated on the blockchain

        if jobInfo["jobStateCode"] == lib.job_state_code["COMPLETED"]:
            logging.error("E: Job is already completed job and its money is received.")
            sys.exit()  # Detects an error on the SLURM side

        is_status, jobInfo = lib.eBlocBrokerFunctionCall(
            lambda: get_job_info(PROVIDER_ID, job_key, index, jobID, received_block_number), 10
        )
        if not is_status:
            sys.exit()

        logging.info(f"Waiting for {count * 15} seconds to pass...")
        time.sleep(15)  # Short sleep here so this loop is not keeping CPU busy //setJobIs_Status may deploy late.

    # sourceCodeHashes of the completed job is obtained from its.writeged event
    is_status, jobInfo = lib.eBlocBrokerFunctionCall(
        lambda: getJobSourceCodeHash(jobInfo, PROVIDER_ID, job_key, index, jobID, received_block_number), 10
    )
    if not is_status:
        sys.exit()

    logging.info(f"jobName={folder_name}")
    with open(f"{results_folder}/slurmJobInfo.out", "w") as stdout:
        command = [
            "scontrol",
            "show",
            "job",
            slurmJobID,
        ]  # cmd: scontrol show job $slurmJobID > $results_folder/slurmJobInfo.out
        subprocess.Popen(command, stdout=stdout)
        logging.info("Writing into slurmJobInfo.out file is completed")

    command = [
        "sacct",
        "-n",
        "-X",
        "-j",
        slurmJobID,
        "--format=Elapsed",
    ]  # cmd: sacct -n -X -j $slurmJobID --format="Elapsed"
    is_status, elapsedTime = execute_shell_command(command, None, True)
    logging.info(f"ElapsedTime={elapsedTime}")

    elapsedTime = elapsedTime.split(":")
    elapsedDay = "0"
    elapsedHour = elapsedTime[0].replace(" ", "")
    elapsedMinute = elapsedTime[1].rstrip()

    if "-" in str(elapsedHour):
        elapsedHour = elapsedHour.split("-")
        elapsedDay = elapsedHour[0]
        elapsedHour = elapsedHour[1]

    elapsedRawTime = int(elapsedDay) * 1440 + int(elapsedHour) * 60 + int(elapsedMinute) + 1
    logging.info(f"ElapsedRawTime={elapsedRawTime}")

    if elapsedRawTime > int(executionDuration[jobID]):
        elapsedRawTime = executionDuration[jobID]

    logging.info(f"finalizedElapsedRawTime={elapsedRawTime}")
    logging.info(f"jobInfo={jobInfo}")
    output_file_name = f"result-{PROVIDER_ID}-{job_key}-{index}.tar.gz"

    # Here we know that job is already completed
    if cloudStorageID == str(lib.StorageID.IPFS.value) or cloudStorageID == str(lib.StorageID.GITHUB.value):
        removeSourceCode(results_folder_prev, results_folder)
        for attempt in range(10):
            command = ["ipfs", "add", "-r", results_folder]  # Uploaded as folder
            is_status, result_ipfs_hash = execute_shell_command(command, None, True)
            if not is_status or result_ipfs_hash == "":
                """ Approach to upload as .tar.gz. Currently not used.
                removeSourceCode(results_folder_prev)
                with open(results_folder_prev + '/modifiedDate.txt') as content_file:
                date = content_file.read().strip()
                command = ['tar', '-N', date, '-jcvf', output_file_name] + glob.glob("*")
                log.write(execute_shell_command(command, None, True))
                command = ['ipfs', 'add', results_folder + '/result.tar.gz']
                is_status, result_ipfs_hash = execute_shell_command(command)
                result_ipfs_hash = result_ipfs_hash.split(' ')[1]
                silentremove(results_folder + '/result.tar.gz')
                """
                logging.error(f"E: Generated new hash return empty. Trying again... Try count: {attempt}")
                time.sleep(5)  # wait 5 second for next step retry to up-try
            else:  # success
                break
        else:  # we failed all the attempts - abort
            sys.exit()

        # dataTransferOut = lib.calculateFolderSize(results_folder, 'd')
        # log.write('dataTransferOut=' + str(dataTransferOut) + ' MB | Rounded=' + str(int(dataTransferOut)) + ' MB')
        result_ipfs_hash = lib.getIpfsParentHash(result_ipfs_hash)
        command = ["ipfs", "pin", "add", result_ipfs_hash]
        is_status, res = execute_shell_command(command, None, True)  # pin downloaded ipfs hash
        print(res)

        command = ["ipfs", "object", "stat", result_ipfs_hash]
        is_status, is_ipfs_hash_exist = execute_shell_command(command, None, True)  # pin downloaded ipfs hash
        for item in is_ipfs_hash_exist.split("\n"):
            if "CumulativeSize" in item:
                dataTransferOut = item.strip().split()[1]
                break

        dataTransferOut = lib.convert_byte_to_mb(dataTransferOut)
        logging.info(f"dataTransferOut={dataTransferOut} MB | Rounded={int(dataTransferOut)} MB")
    if cloudStorageID == str(lib.StorageID.IPFS_MINILOCK.value):
        os.chdir(results_folder)
        with open(f"{results_folder_prev}/modifiedDate.txt") as content_file:
            date = content_file.read().strip()

        command = ["tar", "-N", date, "-jcvf", output_file_name] + glob.glob("*")
        is_status, result = execute_shell_command(command, None, True)
        logging.info(result)
        # cmd: mlck encrypt -f $results_folder/result.tar.gz $miniLockID --anonymous --output-file=$results_folder/result.tar.gz.minilock
        command = [
            "mlck",
            "encrypt",
            "-f",
            f"{results_folder}/result.tar.gz",
            miniLockID,
            "--anonymous",
            f"--output-file={results_folder}/result.tar.gz.minilock",
        ]
        is_status, res = execute_shell_command(command, None, True)
        logging.info(res)
        removeSourceCode(results_folder_prev, results_folder)
        for attempt in range(10):
            command = ["ipfs", "add", f"{results_folder}/result.tar.gz.minilock"]
            is_status, result_ipfs_hash = execute_shell_command(command, None, True)
            result_ipfs_hash = result_ipfs_hash.split(" ")[1]
            if result_ipfs_hash == "":
                logging.error(f"E: Generated new hash returned empty. Trying again... Try count: {attempt}")
                time.sleep(5)  # wait 5 second for next step retry to up-try
            else:  # success
                break
        else:  # we failed all the attempts - abort
            sys.exit()

        # dataTransferOut = lib.calculateFolderSize(results_folder + '/result.tar.gz.minilock', 'f')
        # log.write('dataTransferOut=' + str(dataTransferOut) + ' MB | Rounded=' + str(int(dataTransferOut)) + ' MB')
        logging.info(f"result_ipfs_hash={result_ipfs_hash}")
        command = ["ipfs", "pin", "add", result_ipfs_hash]
        is_status, res = execute_shell_command(command, None, True)
        print(res)
        command = ["ipfs", "object", "stat", result_ipfs_hash]
        is_status, is_ipfs_hash_exist = execute_shell_command(command, None, True)
        for item in is_ipfs_hash_exist.split("\n"):
            if "CumulativeSize" in item:
                dataTransferOut = item.strip().split()[1]
                break

        dataTransferOut = lib.convert_byte_to_mb(dataTransferOut)
        logging.info(f"dataTransferOut={dataTransferOut} MB | Rounded={int(dataTransferOut)} MB")
    elif cloudStorageID == str(lib.StorageID.EUDAT.value):
        logging.info("Entered into Eudat case")
        result_ipfs_hash = ""
        lib.removeFiles(f"{results_folder}/.node-xmlhttprequest*")
        os.chdir(results_folder)
        removeSourceCode(results_folder_prev, results_folder)
        # cmd: tar -jcvf result-$providerID-$index.tar.gz *
        # command = ['tar', '-jcvf', output_file_name] + glob.glob("*")
        # log.write(execute_shell_command(command))
        with open(results_folder_prev + "/modifiedDate.txt") as content_file:
            date = content_file.read().strip()

        command = ["tar", "-N", date, "-jcvf", output_file_name] + glob.glob("*")
        is_status, result = execute_shell_command(command, None, True)
        logging.info(f"Files to be archived using tar: \n {result}")
        dataTransferOut = lib.calculateFolderSize(output_file_name, "f")
        logging.info(f"dataTransferOut={dataTransferOut} MB | Rounded={int(dataTransferOut)} MB")
        for attempt in range(5):
            p, output, err = upload_results_to_eudat(encodedShareToken, output_file_name)
            output = output.strip().decode("utf-8")
            err = err.decode("utf-8")
            if p.returncode != 0 or "<d:error" in output:
                logging.error("E: EUDAT repository did not successfully loaded.")
                logging.error(f"curl failed {p.returncode} {err.decode('utf-8')}. {output}")
                time.sleep(1)  # wait 1 second for next step retry to upload
            else:  # success on upload
                break
        else:  # we failed all the attempts - abort
            sys.exit()
    elif cloudStorageID == str(lib.StorageID.GDRIVE.value):
        result_ipfs_hash = ""
        # cmd: gdrive info $job_key -c $GDRIVE_METADATA # stored for both pipes otherwise its read and lost
        is_status, gdriveInfo = lib.subprocessCallAttempt(
            [lib.GDRIVE, "info", "--bytes", job_key, "-c", lib.GDRIVE_METADATA], 500, 1
        )
        if not is_status:
            return False

        mimeType = lib.getGdriveFileInfo(gdriveInfo, "Mime")
        logging.info(f"mime_type={mimeType}")
        os.chdir(results_folder)
        # if 'folder' in mimeType:  # Received job is in folder format
        removeSourceCode(results_folder_prev, results_folder)
        with open(results_folder_prev + "/modifiedDate.txt", "r") as content_file:
            date = content_file.read().rstrip()

        command = ["tar", "-N", date, "-jcvf", output_file_name] + glob.glob("*")
        is_status, result = execute_shell_command(command, None, True)
        logging.info(result)
        time.sleep(0.25)
        dataTransferOut = lib.calculateFolderSize(output_file_name, "f")
        logging.info(f"dataTransferOut={dataTransferOut} MB | Rounded={int(dataTransferOut)} MB")
        if "folder" in mimeType:  # Received job is in folder format
            logging.info("mimeType=folder")
            # cmd: $GDRIVE upload --parent $job_key result-$providerID-$index.tar.gz -c $GDRIVE_METADATA
            command = [lib.GDRIVE, "upload", "--parent", job_key, output_file_name, "-c", lib.GDRIVE_METADATA]
            is_status, res = lib.subprocessCallAttempt(command, 500)
            logging.info(res)
        elif "gzip" in mimeType:  # Received job is in folder tar.gz
            logging.info("mimeType=tar.gz")
            # cmd: $GDRIVE update $job_key result-$providerID-$index.tar.gz -c $GDRIVE_METADATA
            command = [lib.GDRIVE, "update", job_key, output_file_name, "-c", lib.GDRIVE_METADATA]
            is_status, res = lib.subprocessCallAttempt(command, 500)
            logging.info(res)
        elif "/zip" in mimeType:  # Received job is in zip format
            logging.info("mimeType=zip")
            # cmd: $GDRIVE update $job_key result-$providerID-$index.tar.gz -c $GDRIVE_METADATA
            command = [lib.GDRIVE, "update", job_key, output_file_name, "-c", lib.GDRIVE_METADATA]
            is_status, res = lib.subprocessCallAttempt(command, 500)
            logging.info(res)
        else:
            logging.error("E: Files could not be uploaded")
            sys.exit()

    dataTransferSum = dataTransferIn + dataTransferOut
    logging.info(f"dataTransferIn={dataTransferIn} MB | Rounded={int(dataTransferIn)} MB")
    logging.info(f"dataTransferOut={dataTransferOut} MB | Rounded={int(dataTransferOut)} MB")
    logging.info(f"dataTransferSum={dataTransferSum} MB | Rounded={int(dataTransferSum)} MB")
    process_payment_tx(
        job_key,
        index,
        jobID,
        elapsedRawTime,
        result_ipfs_hash,
        cloudStorageID,
        slurmJobID,
        int(dataTransferIn),
        int(dataTransferOut),
        jobInfo,
    )

    logging.info("=====COMPLETED=====")
    """
    # Removed downloaded code from local since it is not needed anymore
    if os.path.isdir(results_folder_prev):
    shutil.rmtree(results_folder_prev)  # deletes a directory and all its contents.
    """


if __name__ == "__main__":
    job_key = sys.argv[1]
    index = sys.argv[2]
    cloudStorageID = sys.argv[3]
    shareToken = sys.argv[4]
    received_block_number = sys.argv[5]
    folder_name = sys.argv[6]
    slurmJobID = sys.argv[7]

    end_code(job_key, index, cloudStorageID, shareToken, received_block_number, folder_name, slurmJobID)
