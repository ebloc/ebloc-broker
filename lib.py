#!/usr/bin/env python3

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
from datetime import datetime, timedelta
from enum import Enum
from os.path import expanduser
from shutil import copyfile
from typing import Tuple

from dotenv import load_dotenv
from termcolor import colored

import config
from config import logging
from lib_mongodb import add_item
from utils import byte_to_mb, read_json


# enum: https://stackoverflow.com/a/1695250/2402577
def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    reverse = dict((value, key) for key, value in enums.items())
    enums["reverse_mapping"] = reverse
    return type("Enum", (), enums)


def WHERE(back=0):
    try:
        frame = sys._getframe(back + 1)
    except:
        frame = sys._getframe(1)

    return "%s/%s %s()" % (os.path.basename(frame.f_code.co_filename), frame.f_lineno, frame.f_code.co_name)


HOME = expanduser("~")
# Load .env from the given path
load_dotenv(os.path.join(f"{HOME}/.eBlocBroker/", ".env"))

WHOAMI = os.getenv("WHOAMI")
SLURMUSER = os.getenv("SLURMUSER")
EBLOCPATH = os.getenv("EBLOCPATH")  #
RPC_PORT = os.getenv("RPC_PORT")  #
LOG_PATH = os.getenv("LOG_PATH")
GDRIVE = os.getenv("GDRIVE")
OC_USER = os.getenv("OC_USER")
POA_CHAIN = str(os.getenv("POA_CHAIN")).lower() in ("yes", "true", "t", "1")  #
IPFS_USE = str(os.getenv("IPFS_USE")).lower() in ("yes", "true", "t", "1")
EUDAT_USE = str(os.getenv("EUDAT_USE")).lower() in ("yes", "true", "t", "1")

GDRIVE_CLOUD_PATH = f"/home/{WHOAMI}/foo"
GDRIVE_METADATA = f"/home/{WHOAMI}/.gdrive"
IPFS_REPO = f"/home/{WHOAMI}/.ipfs"
# HOME = f"/home/{WHOAMI}"
OWN_CLOUD_PATH = "/oc"

PROGRAM_PATH = "/var/eBlocBroker"
JOBS_READ_FROM_FILE = f"{LOG_PATH}/test.txt"
CANCEL_JOBS_READ_FROM_FILE = f"{LOG_PATH}/cancelledJobs.txt"
BLOCK_READ_FROM_FILE = f"{LOG_PATH}/blockReadFrom.txt"
CANCEL_BLOCK_READ_FROM_FILE = f"{LOG_PATH}/cancelledBlockReadFrom.txt"

if config.w3 is None:
    from imports import connect_to_web3

    connect_to_web3()

PROVIDER_ID = config.w3.toChecksumAddress(os.getenv("PROVIDER_ID"))


class CacheType(Enum):
    PUBLIC = 0
    PRIVATE = 1


class StorageID(Enum):
    IPFS = 0
    EUDAT = 1
    IPFS_MINILOCK = 2
    GITHUB = 3
    GDRIVE = 4
    NONE = 5


class JobStateCodes(Enum):
    SUBMITTED = 0
    PENDING = 1
    RUNNING = 2
    REFUNDED = 3
    CANCELLED = 4
    COMPLETED = 5
    TIMEOUT = 6


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


def get_tx_status(success, output):
    # from pprint import pformat
    logging.info(f"tx_hash={output}")
    receipt = config.w3.eth.waitForTransactionReceipt(output)
    logging.info("Transaction receipt mined: \n")
    # logging.info(pformat(receipt))
    pprint.pprint(dict(receipt))  # delete
    logging.info(f"Was transaction successful? => status={receipt['status']}")
    return receipt


def check_size_of_file_before_download(file_type, key=None):
    if int(file_type) == StorageID.IPFS.value or int(file_type) == StorageID.IPFS_MINILOCK.value:
        if key is None:  # key refers to ipfs_hash
            return False
        pass
    elif int(file_type) == StorageID.EUDAT.value:
        pass
    elif int(file_type) == StorageID.GDRIVE.value:
        pass
    return True


def terminate():
    """ Terminates Driver and all the dependent python programs to it."""
    logging.error(f"E: [{WHERE(1)}] terminate() function is called.")

    # Following line is added, in case ./killall.sh does not work due to sudo.
    # Send the kill signal to all the process groups.
    if config.driver_cancel_process is not None:
        os.killpg(os.getpgid(config.driver_cancel_process.pid), signal.SIGTERM)  # obtained from global variable

    if config.whisper_state_receiver_process is not None:
        # obtained from global variable, # raise SystemExit("Program Exited")
        os.killpg(os.getpgid(config.whisper_state_receiver_process.pid), signal.SIGTERM)

    # Kill all the dependent processes and exit
    output = subprocess.check_output(["bash", "killall.sh"]).decode("utf-8").rstrip()
    logging.info(output)
    sys.exit(1)


def try_except(f):
    """Calls given function inside try/except

    Args:
        f: yield function

    Returns status and output of the function
    """
    try:
        return f()
    except Exception:
        logging.error(f"{WHERE(1)} - {traceback.format_exc()}")
        return False, None


def get_ipfs_cumulative_size(source_code_hash):
    cmd = ["ipfs", "object", "stat", source_code_hash]
    success, is_ipfs_hash_exist = run_command(cmd, None, True)
    for item in is_ipfs_hash_exist.split("\n"):
        if "CumulativeSize" in item:
            return item.strip().split()[1]


def get_ipfs_parent_hash(result_ipfs_hash) -> Tuple[bool, str]:
    """Parses output of 'ipfs add -r path --only-hash' cmd and obtain its parent folder's hash.

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


def get_only_ipfs_hash(path) -> Tuple[bool, str]:
    """Gets only chunk and hash of a given path, do not write to disk.

    Args:
        path: Path of a folder or file

    Returns string that contains the ouput of the run commad.
    """
    if os.path.isdir(path):
        cmd = ["ipfs", "add", "-r", path, "--only-hash", "-H"]
    elif os.path.isfile(path):
        cmd = ["ipfs", "add", path, "--only-hash"]
    else:
        logging.error("E: Requested path does not exist.")
        return False, None

    success, output = run_command(cmd, None, is_exit_flag=True)
    if success:
        success, result_ipfs_hash = try_except(lambda: get_ipfs_parent_hash(output), is_exit_flag=True)

    if not success:
        return False, None

    return True, result_ipfs_hash


def get_ipfs_hash(ipfs_hash, path, is_storage_paid):
    output = subprocess.check_output(["ipfs", "get", ipfs_hash, f"--output={path}"]).decode("utf-8").rstrip()
    logging.info(output)

    if is_storage_paid:
        # Pin downloaded ipfs hash if storage is paid
        output = subprocess.check_output(["ipfs", "pin", "add", ipfs_hash]).decode("utf-8").rstrip()
        logging.info(output)


def is_ipfs_hash_exists(ipfs_hash, attempt_count):
    for attempt in range(attempt_count):
        logging.info(f"Attempting to check IPFS file {ipfs_hash}")
        # IPFS_PATH=$HOME"/.ipfs" && export IPFS_PATH TODO: Probably not required
        timeout_duration = "300"  # Wait max 5 minutes.
        success, ipfs_stat = run_command(["timeout", timeout_duration, "ipfs", "object", "stat", ipfs_hash])
        if not success:
            logging.error(f"E: Failed to find IPFS file: {ipfs_hash}")
        else:
            log(ipfs_stat, "yellow")
            for item in ipfs_stat.split("\n"):
                if "CumulativeSize" in item:
                    cumulative_size = item.strip().split()[1]
            return True, ipfs_stat, int(cumulative_size)
    else:
        return False, None, None


def ipfs_add(self, path):
    if os.path.isdir(path):  # uploaded as folder
        cmd = ["ipfs", "add", "-r", path]
    elif os.path.isfile(path):  # uploaded as file
        cmd = ["ipfs", "add", path]
    else:
        logging.error("E: Requested path does not exist.")
        return False, ""

    for attempt in range(10):
        success, result_ipfs_hash = run_command(cmd, None, True)
        if os.path.isfile(path):
            result_ipfs_hash = result_ipfs_hash.split(" ")[1]

        if not success or not result_ipfs_hash:
            logging.error(f"E: Generated new hash returned empty. Trying again... Try count: {attempt}")
            time.sleep(5)  # Wait 5 seconds for next retry to upload again
        else:  # success
            break
    else:  # Failed all the attempts - abort
        sys.exit(1)

    return True, result_ipfs_hash


def calculate_folder_size(path) -> float:
    """Return the size of the given path in MB."""
    byte_size = 0
    p1 = subprocess.Popen(["du", "-sb", path], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["awk", "{print $1}"], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    # Returns downloaded files size in bytes
    byte_size = p2.communicate()[0].decode("utf-8").strip()
    return byte_to_mb(byte_size)


def printc(text, color="white"):
    print(colored(f"\033[1m{text}\033[0m", color))


def log(text, color="", is_new_line=True, filename=f"{LOG_PATH}/transactions/providerOut.txt"):
    if color != "":
        if is_new_line:
            printc(text)
        else:
            print(colored(f"\033[1m{text}\033[0m", color), end="")
    else:
        if is_new_line:
            print(text)
        else:
            print(text, end="")

    f = open(filename, "a")
    if is_new_line:
        f.write(f"{text}\n")
    else:
        f.write(text)
    f.close()


def subprocess_call_attempt(cmd, attempt_count=1, print_flag=True):
    for count in range(attempt_count):
        try:
            return subprocess.check_output(cmd).decode("utf-8").strip()
        except Exception:
            if not count and print_flag:
                logging.error(f"{WHERE(1)} - {traceback.format_exc()}")

            if count + 1 == attempt_count:
                raise SystemExit
            logging.info(f"try={count}")
            time.sleep(0.1)


def run_command_stdout_to_file(cmd, path, is_exit_flag=False) -> bool:
    with open(path, "w") as stdout:
        try:
            subprocess.Popen(cmd, stdout=stdout)
            logging.info(f"Writing into path is completed => {path}")
        except Exception:
            cmd_str = " ".join(cmd)
            logging.error(f"[{WHERE(1)}] - {traceback.format_exc()} command:\n {cmd_str}")
            raise SystemExit


def run_command(cmd, my_env=None, is_exit_flag=False) -> Tuple[bool, str]:
    output = ""
    try:
        if my_env is None:
            output = subprocess.check_output(cmd).decode("utf-8").strip()
        else:
            output = subprocess.check_output(cmd, env=my_env).decode("utf-8").strip()
    except Exception:
        cmd_str = " ".join(cmd)
        print(output)
        logging.error(f"[{WHERE(1)}] \n {traceback.format_exc()} command:\n {cmd_str}")
        if is_exit_flag:
            terminate()
        return False, output

    return True, output


def silent_remove(path) -> bool:
    # Link: https://stackoverflow.com/a/10840586/2402577
    try:
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)  # deletes a directory and all its contents
        else:
            return False

        logging.info(f"[{WHERE(1)}] - {path} is removed")
        return True
    except Exception:
        logging.error(f"[{WHERE(1)}] - {traceback.format_exc()}")
        return False


def remove_files(file_name):
    if "*" in file_name:
        for f in glob.glob(file_name):
            if not silent_remove(f):
                return False
    else:
        if not silent_remove(file_name):
            return False

    return True


def echo_grep_awk(str_data, grep_str, awk_column):
    """cmd: echo gdrive_info | grep _type | awk \'{print $2}\'"""
    p1 = subprocess.Popen(["echo", str_data], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["grep", grep_str], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    p3 = subprocess.Popen(["awk", "{print $" + awk_column + "}"], stdin=p2.stdout, stdout=subprocess.PIPE)
    p2.stdout.close()
    return p3.communicate()[0].decode("utf-8").strip()


def eblocbroker_function_call(f, attempt):
    for attempt in range(attempt):
        success, output = f()
        if success:
            return True, output
        else:
            logging.error(f"[{WHERE(1)}] E: {output}")
            if output == "notconnected":
                time.sleep(1)
            else:
                return False, output
    else:
        return False, output


def is_ipfs_hash_cached(ipfs_hash):
    p1 = subprocess.Popen(["ipfs", "refs", "local"], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["grep", "-c", ipfs_hash], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    output = p2.communicate()[0].decode("utf-8").strip()
    if output == "1":
        return True
    else:
        return False


def insert_character(string, index, char) -> str:
    return string[:index] + char + string[index:]


def is_process_on(process_name, name, process_count=0) -> bool:
    """Checks wheather the process runs on the background.
    Doc: https://stackoverflow.com/a/6482230/2402577"""
    p1 = subprocess.Popen(["ps", "aux"], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["grep", "-E", process_name], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    p3 = subprocess.Popen(["wc", "-l"], stdin=p2.stdout, stdout=subprocess.PIPE)
    p2.stdout.close()
    output = p3.communicate()[0].decode("utf-8").strip()
    if int(output) > process_count:
        logging.warning(f"{name} is already running.")
        return True
    return False


def is_driver_on() -> bool:
    """ Checks whether driver runs on the background."""
    return is_process_on("python.*[D]river", "Driver", 1)


def is_ipfs_on() -> bool:
    """ Checks whether ipfs runs on the background."""
    return is_process_on("[i]pfs\ daemon", "IPFS")


def is_geth_on():
    """ Checks whether geth runs on the background."""
    port = str(RPC_PORT)
    port = insert_character(port, 1, "]")
    port = insert_character(port, 0, "[")
    return is_process_on(f"geth.*{port}", "Geth")


def preexec_function():
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def is_transaction_passed(tx_hash):
    receipt = config.w3.eth.getTransactionReceipt(tx_hash)
    if receipt is not None:
        if receipt["status"] == 1:
            return True

    return False


# Checks that does IPFS run on the background or not
def is_ipfs_running():
    output = is_ipfs_on()
    if output:
        return True
    else:
        logging.error("E: IPFS does not work on the background.")
        logging.info("* Starting IPFS: nohup ipfs daemon --mount &")
        cmd = ["nohup", "ipfs", "daemon", "--mount"]
        path = f"{LOG_PATH}/ipfs.out"
        with open(path, "w") as stdout:
            subprocess.Popen(cmd, stdout=stdout, stderr=stdout, preexec_fn=os.setpgrp)
            logging.info(f"Writing into {path} is completed.")

        time.sleep(5)
        with open(path, "r") as content_file:
            logging.info(content_file.read())

        # IPFS mounted at: /ipfs
        output = subprocess.check_output(["sudo", "ipfs", "mount", "-f", "/ipfs"]).decode("utf-8").strip()
        logging.info(output)
        return is_ipfs_on()


def is_run_exists_in_tar(tar_path):
    try:
        FNULL = open(os.devnull, "w")
        logging.info(tar_path)
        output = (
            subprocess.check_output(["tar", "ztf", tar_path, "--wildcards", "*/run.sh"], stderr=FNULL).decode("utf-8").strip()
        )
        FNULL.close()
        if output.count("/") == 1:  # Main folder should contain the 'run.sh' file
            logging.info("./run.sh exists under the parent folder")
            return True
        else:
            logging.error("run.sh does not exist under the parent folder")
            return False
    except:
        logging.error("run.sh does not exist under the parent folder")
        return False


def compress_folder(folder_to_share):
    current_path = os.getcwd()
    base_name = os.path.basename(folder_to_share)
    dir_path = os.path.dirname(folder_to_share)
    os.chdir(dir_path)

    # Tar produces different files each time: https://unix.stackexchange.com/a/438330/198423
    # cmd: find exampleFolderToShare -print0 | LC_ALL=C sort -z | GZIP=-n tar --absolute-names --no-recursion --null -T - -zcvf exampleFolderToShare.tar.gz
    p1 = subprocess.Popen(["find", base_name, "-print0"], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["sort", "-z"], stdin=p1.stdout, stdout=subprocess.PIPE, env={"LC_ALL": "C"})
    p1.stdout.close()
    p3 = subprocess.Popen(
        [
            "tar",
            "--mode=a+rwX",
            "--owner=0",
            "--group=0",
            "--numeric-owner",
            "--absolute-names",
            "--no-recursion",
            "--null",
            "-T",
            "-",
            "-zcvf",
            f"{base_name}.tar.gz",
        ],
        stdin=p2.stdout,
        stdout=subprocess.PIPE,
        env={"PIGZ": "-n"},
    )
    p2.stdout.close()
    p3.communicate()

    tar_hash = subprocess.check_output(["md5sum", f"{base_name}.tar.gz"]).decode("utf-8").strip()
    tar_hash = tar_hash.split(" ", 1)[0]
    shutil.move(f"{base_name}.tar.gz", f"{tar_hash}.tar.gz")
    os.chdir(current_path)
    return tar_hash


def _sbatch_call(logged_job, requester_id, results_folder, results_folder_prev, dataTransferIn, source_code_hash_list, job_info):
    job_key = logged_job.args["jobKey"]
    index = logged_job.args["index"]
    cloud_storage_id = logged_job.args["cloudStorageID"][0]  # 0 indicated maps to sourceCode
    job_info = job_info[0]
    job_id = 0  # Base job_id for them workflow

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

    logging.info(f"job_received_block_number={logged_job.blockNumber}")
    f = open(f"{results_folder_prev}/receivedBlockNumber.txt", "w")
    f.write(f"{logged_job.blockNumber}")
    f.close()

    logging.info("Adding recevied job into mongodb database.")
    # Adding job_key info along with its cacheDuration into mongodb
    add_item(job_key, source_code_hash_list, requester_id, timestamp, cloud_storage_id, job_info)

    # TODO: update as used_dataTransferIn value
    f = f"{results_folder_prev}/dataTransferIn.json"
    success, data = read_json(f)
    if success:
        dataTransferIn = data["dataTransferIn"]
    else:
        data = {}
        data["dataTransferIn"] = dataTransferIn
        with open(f, "w") as outfile:
            json.dump(data, outfile)

    # logging.info(dataTransferIn)
    time.sleep(0.25)
    # seperator character is ;
    sbatch_file_path = f"{results_folder}/{job_key}*{index}*{cloud_storage_id}*{logged_job.blockNumber}.sh"
    copyfile(f"{results_folder}/run.sh", sbatch_file_path)

    job_core_num = str(job_info["core"][job_id])
    # Client's requested seconds to run his/her job, 1 minute additional given.
    execution_time_second = timedelta(seconds=int((job_info["executionDuration"][job_id] + 1) * 60))
    d = datetime(1, 1, 1) + execution_time_second
    time_limit = str(int(d.day) - 1) + "-" + str(d.hour) + ":" + str(d.minute)
    logging.info(f"time_limit={time_limit} | requested_core_num={job_core_num}")
    # Give permission to user that will send jobs to Slurm.
    subprocess.check_output(["sudo", "chown", "-R", requester_id, results_folder])

    for attempt in range(10):
        try:
            # SLURM submit job, Real mode -N is used. For Emulator-mode -N use 'sbatch -c'
            # cmd: sudo su - $requester_id -c "cd $results_folder && sbatch -c$job_core_num $results_folder/${job_key}*${index}*${cloud_storage_id}.sh --mail-type=ALL
            job_id = (
                subprocess.check_output(
                    [
                        "sudo",
                        "su",
                        "-",
                        requester_id,
                        "-c",
                        f'cd {results_folder} && sbatch -N {job_core_num} "{sbatch_file_path}" --mail-type=ALL',
                    ]
                )
                .decode("utf-8")
                .strip()
            )
            time.sleep(1)  # Wait 1 second for Slurm idle core to be updated.
        except subprocess.CalledProcessError as e:
            logging.error(e.output.decode("utf-8").strip())
            success, output = run_command(["sacctmgr", "remove", "user", "where", f"user={requester_id}", "--immediate"])
            success, output = run_command(["sacctmgr", "add", "account", requester_id, "--immediate"])
            success, output = run_command(
                ["sacctmgr", "create", "user", requester_id, f"defaultaccount={requester_id}", "adminlevel=[None]", "--immediate"]
            )
        else:
            break
    else:
        sys.exit(1)

    slurm_job_id = job_id.split()[3]
    logging.info(f"slurm_job_id={slurm_job_id}")
    try:
        # cmd: scontrol update jobid=$slurm_job_id TimeLimit=$time_limit
        subprocess.run(["scontrol", "update", f"jobid={slurm_job_id}", f"TimeLimit={time_limit}"], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        logging.error(e.output.decode("utf-8").strip())

    if not slurm_job_id.isdigit():
        logging.error("E: Detects an error on the SLURM side. slurm_job_id is not a digit.")
        return False

    return True


def remove_empty_files_and_folders(results_folder) -> None:
    """Remove empty files if exists"""
    p1 = subprocess.Popen(["find", results_folder, "-size", "0", "-print0"], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["xargs", "-0", "-r", "rm"], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    p2.communicate()

    # Removes empty folders
    subprocess.run(["find", results_folder, "-type", "d", "-empty", "-delete"])
    p1 = subprocess.Popen(["find", results_folder, "-type", "d", "-empty", "-print0"], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["xargs", "-0", "-r", "rmdir"], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    p2.communicate()
