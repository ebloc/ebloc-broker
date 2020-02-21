#!/usr/bin/env python3

import binascii
import glob
import json
import os
import pprint
import shutil
import signal
import subprocess
import sys
import time
import traceback
from enum import Enum
from os.path import expanduser
from shutil import copyfile
from typing import Tuple

import base58
from colored import fg, stylize
from dotenv import load_dotenv
from termcolor import colored

import config
from config import load_log
from lib_mongodb import add_item


# enum: https://stackoverflow.com/a/1695250/2402577
def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    reverse = dict((value, key) for key, value in enums.items())
    enums["reverse_mapping"] = reverse
    return type("Enum", (), enums)


home = expanduser("~")
load_dotenv(os.path.join(f"{home}/.eBlocBroker/", ".env"))  # Load .env from the given path

WHOAMI = os.getenv("WHOAMI")
EBLOCPATH = os.getenv("EBLOCPATH")
LOG_PATH = os.getenv("LOG_PATH")
PROVIDER_ID = os.getenv("PROVIDER_ID")
GDRIVE = os.getenv("GDRIVE")
RPC_PORT = os.getenv("RPC_PORT")
OC_USER = os.getenv("OC_USER")
POA_CHAIN = str(os.getenv("POA_CHAIN")).lower() in ("yes", "true", "t", "1")
IPFS_USE = str(os.getenv("IPFS_USE")).lower() in ("yes", "true", "t", "1")
EUDAT_USE = str(os.getenv("EUDAT_USE")).lower() in ("yes", "true", "t", "1")

GDRIVE_CLOUD_PATH = f"/home/{WHOAMI}/foo"
GDRIVE_METADATA = f"/home/{WHOAMI}/.gdrive"
IPFS_REPO = f"/home/{WHOAMI}/.ipfs"
HOME = f"/home/{WHOAMI}"
OWN_CLOUD_PATH = "/oc"

PROGRAM_PATH = "/var/eBlocBroker"
JOBS_READ_FROM_FILE = f"{LOG_PATH}/test.txt"
CANCEL_JOBS_READ_FROM_FILE = f"{LOG_PATH}/cancelledJobs.txt"
BLOCK_READ_FROM_FILE = f"{LOG_PATH}/blockReadFrom.txt"
CANCEL_BLOCK_READ_FROM_FILE = f"{LOG_PATH}/cancelledBlockReadFrom.txt"

logging = load_log()  # After LOG_PATH is set


class CacheType(Enum):
    PUBLIC = 0
    PRIVATE = 1
    """ delete
    NONE    = 2
    IPFS    = 3
    """


class StorageID(Enum):
    IPFS = 0
    EUDAT = 1
    IPFS_MINILOCK = 2
    GITHUB = 3
    GDRIVE = 4
    NONE = 5


# Creates the hashmap.
job_state_code = {}

# Add keys to the hashmap # https://slurm.schedmd.com/squeue.html
# Initial state
job_state_code["SUBMITTED"] = 0
# Indicates when a request is receieved by the provider. The job is waiting for resource allocation. It will eventually run.
job_state_code["PENDING"] = 1
# The job currently is allocated to a node and is running. Corresponding data files are downloaded and verified.*/
job_state_code["RUNNING"] = 2
# Indicates if job is refunded */
job_state_code["REFUNDED"] = 3
# Job was explicitly cancelled by the requester or system administrator. The job may or may not have been initiated. Set by the requester
job_state_code["CANCELLED"] = 4
# The job has completed successfully and deposit is paid to the provider
job_state_code["COMPLETED"] = 5
# Job terminated upon reaching its time limit.
job_state_code["TIMEOUT"] = 6
job_state_code["COMPLETED_WAITING_ADDITIONAL_DATA_TRANSFER_OUT_DEPOSIT"] = 6

inv_job_state_code = {v: k for k, v in job_state_code.items()}

Qm = b"\x12 "
empty_bytes32 = b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"


def get_tx_status(status, result):
    print("tx_hash=" + result)
    receipt = config.w3.eth.waitForTransactionReceipt(result)
    print("Transaction receipt mined: \n")
    pprint.pprint(dict(receipt))
    print("Was transaction successful?")
    pprint.pprint(receipt["status"])
    return receipt


def checkSizeOfFileToDownload(file_type, key=None):
    if int(file_type) == StorageID.IPFS.value or int(file_type) == StorageID.IPFS_MINILOCK.value:
        if key is None:  # key refers to ipfs_hash
            return False
        pass
    elif int(file_type) == StorageID.EUDAT.value:
        pass
    elif int(file_type) == StorageID.GDRIVE.value:
        pass

    return True


def commitFolder():
    pass


def terminate():
    """ Terminates Driver and all the dependent driver python programs
    """
    logging.error("E: terminate() function is called.")
    # Following line is added, in case ./killall.sh does not work due to sudo.
    # Send the kill signal to all the process groups.
    if config.driver_cancel_process is not None:
        os.killpg(os.getpgid(config.driver_cancel_process.pid), signal.SIGTERM)  # obtained from global variable

    if config.whisper_state_receiver_process is not None:
        os.killpg(
            os.getpgid(config.whisper_state_receiver_process.pid), signal.SIGTERM
        )  # obtained from global variable
        # raise SystemExit("Program Exited")

    subprocess.run(["sudo", "bash", "killall.sh"])  # Kill all dependent processes and exit
    sys.exit()


def try_except(f, is_exit_flag=False):
    """Calls given function inside try/except

    Args:
        f: yield function

    Returns status and result of the function
    """
    try:
        return f()
    except Exception:
        logging.error(traceback.format_exc())
        return False, None


def get_idle_cores(print_flag=True):
    # cmd: sinfo -h -o%C
    status, core_info = execute_shell_command(["sinfo", "-h", "-o%C"])
    core_info = core_info.split("/")
    if len(core_info) != 0:
        allocated_cores = core_info[0]
        idle_cores = core_info[1]
        other_cores = core_info[2]
        total_number_of_cores = core_info[3]
        if print_flag:
            logging.info(
                f"AllocatedCores={allocated_cores} |IdleCores={idle_cores} |OtherCores={other_cores}| TotalNumberOfCores={total_number_of_cores}"
            )

    else:
        logging.error("sinfo is emptry string.")
        idle_cores = None

    return idle_cores


def getIpfsParentHash(result_ipfs_hash):
    """Parses output of 'ipfs add -r path --only-hash' command and obtain its parent folder's hash.

    Args:
        result_ipfs_hash: String generated by the 'ipfs add -r path --only-hash'

    Returns IPFS hash of the parent directory.
    """
    # cmd: echo result_ipfs_hash | tail -n1 | awk '{print $2}'
    p1 = subprocess.Popen(["echo", result_ipfs_hash], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["tail", "-n1"], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    p3 = subprocess.Popen(["awk", "{print $2}"], stdin=p2.stdout, stdout=subprocess.PIPE)
    p2.stdout.close()
    result_ipfs_hash = p3.communicate()[0].decode("utf-8").strip()
    logging.info(f"result_ipfs_hash={result_ipfs_hash}")
    return True, result_ipfs_hash


def getOnlyIpfsHash(path):
    """Gets oynly chunk and hash of a given path- do not write to disk.

    Args:
        path: Path of a folder or file

    Returns string that contains the ouput of the run commad.
    """
    if os.path.isdir(path):
        command = ["ipfs", "add", "-r", path, "--only-hash", "-H"]
    elif os.path.isfile(path):
        command = ["ipfs", "add", path, "--only-hash"]
    else:
        logging.error("E: Requested path does not exist.")
        return False, None

    status, result = execute_shell_command(command, None, is_exit_flag=True)
    status, result_ipfs_hash = try_except(lambda: getIpfsParentHash(result), is_exit_flag=True)
    if not status:
        return False, None

    return True, result_ipfs_hash


def getIpfsHash(ipfsHash, resultsFolder, storagePaid):
    # TODO try -- catch yap code run olursa ayni dosya'ya get ile dosyayi cekemiyor
    # cmd: ipfs get $ipfsHash --output=$resultsFolder
    res = (
        subprocess.check_output(["ipfs", "get", ipfsHash, "--output=" + resultsFolder]).decode("utf-8").strip()
    )  # Wait Max 5 minutes.
    print(res)

    # TODO: pin if storage is paid
    if storagePaid:
        res = (
            subprocess.check_output(["ipfs", "pin", "add", ipfsHash]).decode("utf-8").strip()
        )  # pin downloaded ipfs hash
        logging.info(res)


def isIpfsHashExists(ipfsHash, attemptCount):
    for attempt in range(attemptCount):
        logging.info(f"Attempting to check IPFS file {ipfsHash}")
        # IPFS_PATH=$HOME"/.ipfs" && export IPFS_PATH TODO: Probably not required
        # cmd: timeout 300 ipfs object stat $jobKey
        status, ipfs_stat = execute_shell_command(
            ["timeout", "300", "ipfs", "object", "stat", ipfsHash]
        )  # Wait Max 5 minutes.
        if not status:
            logging.error(f"E: Failed to find IPFS file: {ipfsHash}")
        else:
            logging.info(ipfs_stat)
            for item in ipfs_stat.split("\n"):
                if "CumulativeSize" in item:
                    cumulativeSize = item.strip().split()[1]
            return True, ipfs_stat, cumulativeSize
    else:
        return False, None, None


def calculateFolderSize(path, pathType):
    """Return the size of the given path in MB."""
    byte_size = 0
    if pathType == "f":
        byte_size = os.path.getsize(path)  # Returns downloaded files size in bytes
    elif pathType == "d":
        p1 = subprocess.Popen(["du", "-sb", path], stdout=subprocess.PIPE)
        p2 = subprocess.Popen(["awk", "{print $1}"], stdin=p1.stdout, stdout=subprocess.PIPE)
        p1.stdout.close()
        byte_size = p2.communicate()[0].decode("utf-8").strip()  # Returns downloaded files size in bytes

    return convert_byte_to_mb(byte_size)


def convertStringToBytes32(hash_string):
    print(hash_string)
    bytes_array = base58.b58decode(hash_string)
    return binascii.hexlify(bytes_array).decode("utf-8")


def convertBytes32ToString(bytes_array):
    return base58.b58encode(bytes_array).decode("utf-8")


def convertBytes32ToIpfs(bytes_array):
    """Convert bytes_array into IPFS hash format."""
    merge = Qm + bytes_array
    return base58.b58encode(merge).decode("utf-8")


def convertIpfsToBytes32(hash_string):
    bytes_array = base58.b58decode(hash_string)
    b = bytes_array[2:]
    return binascii.hexlify(b).decode("utf-8")


def printc(my_string, color=""):
    print(stylize(my_string, fg(color)))


def log(my_string, color="", newLine=True, file_name=f"{LOG_PATH}/transactions/providerOut.txt"):
    if color != "":
        if newLine:
            print(colored(my_string, color))
        else:
            print(colored(my_string, color), end="")
    else:
        if newLine:
            print(my_string)
        else:
            print(my_string, end="")

    f = open(file_name, "a")
    if newLine:
        f.write(my_string + "\n")
    else:
        f.write(my_string)

    f.close()


def subprocess_call_attempt(command, attempt_count, print_flag=0):
    for count in range(attempt_count):
        try:
            result = subprocess.check_output(command).decode("utf-8").strip()
        except Exception:
            time.sleep(0.1)
            if count == 0 and print_flag == 0:
                logging.error(traceback.format_exc())
        else:
            return True, result
    else:
        return False, ""


def execute_shell_command(command, my_env=None, is_exit_flag=False) -> Tuple[bool, str]:
    result = ""
    try:
        if my_env is None:
            result = subprocess.check_output(command).decode("utf-8").strip()
        else:
            result = subprocess.check_output(command, env=my_env).decode("utf-8").strip()
    except Exception:
        logging.error(traceback.format_exc())
        if is_exit_flag:
            terminate()
        return False, result

    return True, result


def silent_remove(path) -> bool:
    # Link: https://stackoverflow.com/a/10840586/2402577
    try:
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
        else:
            return False

        logging.info(f"{path} is removed")
        return True
    except Exception:
        logging.error(traceback.format_exc())
        return False


def removeFiles(filename):
    if "*" in filename:
        for f in glob.glob(filename):
            if not silent_remove(f):
                return False
    else:
        if not silent_remove(filename):
            return False

    return True


def convert_byte_to_mb(byte_size):
    return int(byte_size) * 0.000001


def echo_grep_awk(str_data, grep_str, awkColumn):
    p1 = subprocess.Popen(["echo", str_data], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["grep", grep_str], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    p3 = subprocess.Popen(["awk", "{print $" + awkColumn + "}"], stdin=p2.stdout, stdout=subprocess.PIPE)
    p2.stdout.close()
    return p3.communicate()[0].decode("utf-8").strip()


def gdrive_size(
    key, mimeType, folderName, gdrive_info, results_folder_prev, source_code_hash_list, shouldAlreadyCached
):
    sourceCode_key = None
    if "folder" in mimeType:
        job_key_list = []
        # rounded_size = 0
        size_to_download = 0
        command = ["gdrive", "list", "--query", "'" + key + "'" + " in parents"]
        status, result = execute_shell_command(command, None, True)

        dataFiles_json_id = echo_grep_awk(result, "meta_data.json", "1")
        status, res = subprocess_call_attempt(
            ["gdrive", "download", "--recursive", dataFiles_json_id, "--force", "--path", results_folder_prev], 10
        )
        if not status:
            return False

        # key for the sourceCode elimination result*.tar.gz files
        key = echo_grep_awk(result, f"{folderName}.tar.gz", "1")
        sourceCode_key = key
        status, gdrive_info = subprocess_call_attempt(["gdrive", "info", "--bytes", key, "-c", GDRIVE_METADATA], 10)
        if not status:
            return False

        md5sum = get_gdrive_file_info(gdrive_info, "Md5sum")
        if md5sum != source_code_hash_list[0].decode("utf-8"):
            # Checks md5sum obtained from gdrive and given by the user
            logging.info("E: md5sum does not match with the provided data[0]")
            return False, 0, [], sourceCode_key

        byte_size = int(get_gdrive_file_info(gdrive_info, "Size"))
        logging.info(f"sourceCodeHash[0]_size={byte_size} bytes")
        if not shouldAlreadyCached[source_code_hash_list[0].decode("utf-8")]:
            size_to_download = byte_size

        logging.info(f"meta_data_path={results_folder_prev}/meta_data.json")
        with open(f"{results_folder_prev}/meta_data.json") as json_file:
            meta_data = json.load(json_file)

        for idx, (k, v) in enumerate(meta_data.items(), start=1):
            job_key_list.append(str(v))
            _key = str(v)
            status, gdrive_info = subprocess_call_attempt(
                ["gdrive", "info", "--bytes", _key, "-c", GDRIVE_METADATA], 10
            )
            if not status:
                return False

            md5sum = get_gdrive_file_info(gdrive_info, "Md5sum")
            if md5sum != source_code_hash_list[idx].decode("utf-8"):
                # Checks md5sum obtained from gdrive and given by the user
                print(idx)
                logging.error(
                    f"md5sum={md5sum} | given={source_code_hash_list[idx].decode('utf-8')} \n"
                    f"E: md5sum does not match with the provided data[{idx}]"
                )
                return False, 0, [], sourceCode_key

            _size = int(get_gdrive_file_info(gdrive_info, "Size"))
            logging.info(f"sourceCodeHash[{idx}]_size={_size} bytes")
            byte_size += _size
            if not shouldAlreadyCached[source_code_hash_list[idx].decode("utf-8")]:
                size_to_download += _size

        ret_size = int(convert_byte_to_mb(size_to_download))
        logging.info(f"Total_size={byte_size} bytes | Size to download={size_to_download} bytes ==> {ret_size} MB")
        return True, ret_size, job_key_list, sourceCode_key
    else:
        return False, 0, [], sourceCode_key

    """
    elif 'gzip' in mimeType:
        byte_size = lib.get_gdrive_file_info(gdrive_info, 'Size')
        rounded_size = int(convert_byte_to_mb(byte_size))
    """


def getMd5sum(gdrive_info):
    # cmd: echo gdrive_info | grep \'Mime\' | awk \'{print $2}\'
    return echo_grep_awk(gdrive_info, "Md5sum", "2")


def get_gdrive_file_info(gdrive_info, _type):
    # cmd: echo gdrive_info | grep _type | awk \'{print $2}\'
    return echo_grep_awk(gdrive_info, _type, "2")


def eblocbroker_function_call(f, _attempt):
    for attempt in range(_attempt):
        status, result = f()
        if status:
            return True, result
        else:
            logging.error(f"E: {result}")
            if result == "notconnected":
                time.sleep(1)
            else:
                return False, result
    else:
        return False, result


def isIpfsHashCached(ipfsHash):
    # cmd: ipfs refs local | grep -c 'Qmc2yZrduQapeK47vkNeT5pCYSXjsZ3x6yzK8an7JLiMq2'
    p1 = subprocess.Popen(["ipfs", "refs", "local"], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["grep", "-c", ipfsHash], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    out = p2.communicate()[0].decode("utf-8").strip()
    if out == "1":
        return True
    else:
        return False


def isSlurmOn():
    """
    Checks whether Slurm runs on the background or not, if not runs slurm
    """
    logging.info("Checking Slurm... ")
    while True:
        subprocess.run(["bash", "checkSinfo.sh"])
        with open(f"{LOG_PATH}/checkSinfoOut.txt", "r") as content_file:
            check = content_file.read()

        if "PARTITION" not in str(check):
            logging.error("E: sinfo returns emprty string, please run:\nsudo ./runSlurm.sh\n")
            logging.error(f"E: {check}")
            logging.info("Starting Slurm... \n")
            subprocess.run(["sudo", "bash", "runSlurm.sh"])
        elif "sinfo: error" in str(check):
            logging.error(f"Error on munged: \n{check}")
            logging.error("Please Do:\n")
            logging.error("sudo munged -f")
            logging.error("/etc/init.d/munge start")
        else:
            logging.info("Done")
            break


def preexec_function():
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def is_transaction_passed(tx_hash):
    receipt = config.w3.eth.getTransactionReceipt(tx_hash)
    if receipt is not None:
        if receipt["status"] == 1:
            return True

    return False


# Checks that does IPFS run on the background or not
def is_ipfs_on():
    # cmd: ps aux | grep '[i]pfs daemon' | wc -l
    p1 = subprocess.Popen(["ps", "aux"], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["grep", "[i]pfs\ daemon"], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    p3 = subprocess.Popen(["wc", "-l"], stdin=p2.stdout, stdout=subprocess.PIPE)
    p2.stdout.close()
    check = p3.communicate()[0].decode("utf-8").strip()
    if int(check) == 0:
        logging.error("E: IPFS does not work on the background.")
        logging.info("* Starting IPFS: nohup ipfs daemon --mount &")
        with open(f"{LOG_PATH}/ipfs.out", "w") as stdout:
            subprocess.Popen(
                ["nohup", "ipfs", "daemon", "--mount"], stdout=stdout, stderr=stdout, preexec_fn=os.setpgrp
            )

        time.sleep(5)
        with open(f"{LOG_PATH}/ipfs.out", "r") as content_file:
            logging.info(content_file.read())

        # IPFS mounted at: /ipfs //cmd: sudo ipfs mount -f /ipfs
        res = subprocess.check_output(["sudo", "ipfs", "mount", "-f", "/ipfs"]).decode("utf-8").strip()
        logging.info(res)
    else:
        logging.info("IPFS is already on.")


def isRunExistInTar(tar_path):
    try:
        FNULL = open(os.devnull, "w")
        print(tar_path)
        res = (
            subprocess.check_output(["tar", "ztf", tar_path, "--wildcards", "*/run.sh"], stderr=FNULL)
            .decode("utf-8")
            .strip()
        )
        FNULL.close()
        if res.count("/") == 1:  # Main folder should contain the 'run.sh' file
            logging.info("./run.sh exists under the parent folder")
            return True
        else:
            logging.error("run.sh does not exist under the parent folder")
            return False
    except:
        logging.error("run.sh does not exist under the parent folder")
        return False


def compress_folder(folderToShare):
    current_path = os.getcwd()

    base_name = os.path.basename(folderToShare)
    dir_path = os.path.dirname(folderToShare)
    os.chdir(dir_path)
    subprocess.run(["chmod", "-R", "777", base_name])
    # Tar produces different files each time: https://unix.stackexchange.com/a/438330/198423
    # find exampleFolderToShare -print0 | LC_ALL=C sort -z | GZIP=-n tar --absolute-names --no-recursion --null -T - -zcvf exampleFolderToShare.tar.gz
    p1 = subprocess.Popen(["find", base_name, "-print0"], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["sort", "-z"], stdin=p1.stdout, stdout=subprocess.PIPE, env={"LC_ALL": "C"})
    p1.stdout.close()
    p3 = subprocess.Popen(
        ["tar", "--absolute-names", "--no-recursion", "--null", "-T", "-", "-zcvf", f"{base_name}.tar.gz"],
        stdin=p2.stdout,
        stdout=subprocess.PIPE,
        env={"GZIP": "-n"},
    )
    p2.stdout.close()
    p3.communicate()

    # status, ipfsHash = getOnlyIpfsHash(base_name + '.tar.gz')
    # print('ipfsHash=' + ipfsHash)

    # subprocess.run(['sudo', 'tar', 'zcf', base_name + '.tar.gz', base_name])
    tar_hash = subprocess.check_output(["md5sum", f"{base_name}.tar.gz"]).decode("utf-8").strip()
    tar_hash = tar_hash.split(" ", 1)[0]
    shutil.move(f"{base_name}.tar.gz", f"{tar_hash}.tar.gz")
    os.chdir(current_path)
    return tar_hash


def sbatchCall(
    loggedJob,
    shareToken,
    requesterID,
    resultsFolder,
    results_folder_prev,
    dataTransferIn,
    source_code_hash_list,
    jobInfo,
):
    jobKey = loggedJob.args["jobKey"]
    index = loggedJob.args["index"]
    cloudStorageID = loggedJob.args["cloudStorageID"][0]  # cloudStorageID for the sourceCode
    jobInfo = jobInfo[0]
    jobID = 0  # workFlowID

    # from contractCalls.get_job_info import get_job_info
    from datetime import datetime, timedelta

    # cmd: date --date=1 seconds +%b %d %k:%M:%S %Y
    date = (
        subprocess.check_output(["date", "--date=" + "1 seconds", "+%b %d %k:%M:%S %Y"], env={"LANG": "en_us_88591"})
        .decode("utf-8")
        .strip()
    )
    logging.info(f"Date={date}")
    f = open(f"{results_folder_prev}/modified_date.txt", "w")
    f.write(f"{date}\n")
    f.close()
    # cmd: echo date | date +%s
    p1 = subprocess.Popen(["echo", date], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["date", "+%s"], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    timestamp = p2.communicate()[0].decode("utf-8").strip()
    logging.info(f"Timestamp={timestamp}")
    f = open(f"{results_folder_prev}/timestamp.txt", "w")
    f.write(f"{timestamp}")
    f.close()

    logging.info(f"job_received_block_number={loggedJob.blockNumber}")
    f = open(f"{results_folder_prev}/receivedBlockNumber.txt", "w")
    f.write(f"{loggedJob.blockNumber}")
    f.close()

    logging.info("Adding recevied job into mongodb database.")
    # Adding jobKey info along with its cacheDuration into mongodb
    add_item(jobKey, source_code_hash_list, requesterID, timestamp, cloudStorageID, jobInfo)

    # TODO: update as used_dataTransferIn value
    if os.path.isfile(f"{results_folder_prev}/dataTransferIn.txt"):
        with open(results_folder_prev + "/dataTransferIn.txt") as json_file:
            data = json.load(json_file)
            dataTransferIn = data["dataTransferIn"]
    else:
        data = {}
        data["dataTransferIn"] = dataTransferIn
        with open(f"{results_folder_prev}/dataTransferIn.txt", "w") as outfile:
            json.dump(data, outfile)

    # print(dataTransferIn)
    time.sleep(0.25)
    """ TODO: delete check is done one the upper level
    if not os.path.isfile(resultsFolder + '/run.sh'):
        logging.error(resultsFolder + '/run.sh does not exist')
        return False
    """
    sbatch_file_path = f"{resultsFolder}/{jobKey}*{index}*{cloudStorageID}*{shareToken}*{loggedJob.blockNumber}.sh"
    copyfile(f"{resultsFolder}/run.sh", sbatch_file_path)

    # jobID = 0 # Base jobID
    job_core_num = str(jobInfo["core"][jobID])
    # Client's requested seconds to run his/her job, 1 minute additional given.
    executionTimeSecond = timedelta(seconds=int((jobInfo["executionDuration"][jobID] + 1) * 60))
    d = datetime(1, 1, 1) + executionTimeSecond
    time_limit = str(int(d.day) - 1) + "-" + str(d.hour) + ":" + str(d.minute)
    logging.info(f"time_limit={time_limit} | requested_core_num={job_core_num}")
    # Give permission to user that will send jobs to Slurm.
    subprocess.check_output(["sudo", "chown", "-R", requesterID, resultsFolder])

    for attempt in range(10):
        try:
            # SLURM submit job, Real mode -N is used. For Emulator-mode -N use 'sbatch -c'
            # cmd: sudo su - $requesterID -c "cd $resultsFolder && sbatch -c$job_core_num $resultsFolder/${jobKey}*${index}*${cloudStorageID}*$shareToken.sh --mail-type=ALL
            jobID = (
                subprocess.check_output(
                    [
                        "sudo",
                        "su",
                        "-",
                        requesterID,
                        "-c",
                        f"cd {resultsFolder} && sbatch -N {job_core_num} {sbatch_file_path} --mail-type=ALL",
                    ]
                )
                .decode("utf-8")
                .strip()
            )
            time.sleep(1)  # Wait 1 second for Slurm idle core to be updated.
        except subprocess.CalledProcessError as e:
            logging.error(e.output.decode("utf-8").strip())
            # sacctmgr remove user where user=$USERNAME --immediate
            status, res = execute_shell_command(
                ["sacctmgr", "remove", "user", "where", f"user={requesterID}", "--immediate"]
            )
            # sacctmgr add account $USERNAME --immediate
            status, res = execute_shell_command(["sacctmgr", "add", "account", requesterID, "--immediate"])
            # sacctmgr create user $USERNAME defaultaccount=$USERNAME adminlevel=[None] --immediate
            status, res = execute_shell_command(
                [
                    "sacctmgr",
                    "create",
                    "user",
                    requesterID,
                    f"defaultaccount={requesterID}",
                    "adminlevel=[None]",
                    "--immediate",
                ]
            )
        else:
            break
    else:
        sys.exit()

    slurmJobID = jobID.split()[3]
    logging.info(f"slurmJobID={slurmJobID}")
    try:
        # cmd: scontrol update jobid=$slurmJobID TimeLimit=$time_limit
        subprocess.run(
            ["scontrol", "update", f"jobid={slurmJobID}", f"TimeLimit={time_limit}"], stderr=subprocess.STDOUT
        )
    except subprocess.CalledProcessError as e:
        logging.error(e.output.decode("utf-8").strip())

    if not slurmJobID.isdigit():
        # Detects an error on the SLURM side
        logging.error("E: slurm_jobID is not a digit.")
        return False

    return True
