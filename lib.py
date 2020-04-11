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
from shutil import copyfile
from typing import Tuple

from termcolor import colored

import config
import libs.mongodb as mongodb
from config import bp, logging  # noqa: F401
from settings import WHERE, init_env
from utils import byte_to_mb, generate_md5sum, read_json


# enum: https://stackoverflow.com/a/1695250/2402577
def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    reverse = dict((value, key) for key, value in enums.items())
    enums["reverse_mapping"] = reverse
    return type("Enum", (), enums)


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


job_state_code = {}

# add keys to the hashmap # https://slurm.schedmd.com/squeue.html
# initial state
job_state_code["SUBMITTED"] = 0
# indicates when a request is receieved by the provider. The job is waiting for resource allocation. It will eventually run.
job_state_code["PENDING"] = 1
# The job currently is allocated to a node and is running. Corresponding data files are downloaded and verified.*/
job_state_code["RUNNING"] = 2
# indicates if job is refunded */
job_state_code["REFUNDED"] = 3
# Job was explicitly cancelled by the requester or system administrator. The job may or may not have been initiated. Set by the requester
job_state_code["CANCELLED"] = 4
# The job has completed successfully and deposit is paid to the provider
job_state_code["COMPLETED"] = 5
# Job terminated upon reaching its time limit.
job_state_code["TIMEOUT"] = 6
job_state_code["COMPLETED_WAITING_ADDITIONAL_DATA_TRANSFER_OUT_DEPOSIT"] = 6

inv_job_state_code = {v: k for k, v in job_state_code.items()}


def printc(text, color="white"):
    print(colored(f"\033[1m{text}\033[0m", color))


def session_start_msg(slurm_user, columns=100):
    log(
        "=" * int(int(columns) / 2 - 12) + " provider session starts " + "=" * int(int(columns) / 2 - 12), "cyan",
    )
    printc(f"slurm_user={slurm_user} ] provider_address={PROVIDER_ID}", "blue")


def run_driver_cancel():
    """Runs driver_cancel daemon on the background."""
    if not is_process_on("python.*[d]riverCancel", "driverCancel"):
        # running driver_cancel.py on the background if it is not already
        config.driver_cancel_process = subprocess.Popen(["python3", "driver_cancel.py"])


def run_whisper_state_receiver():
    env = init_env()
    """Runs driverReceiver daemon on the background."""
    if not os.path.isfile(f"{env.HOME}/.eBlocBroker/whisperInfo.txt"):
        # first time running
        logging.info(f"run: {env.EBLOCPATH}/scripts/whisper_initialize.py")
        terminate()
    else:
        try:
            data = read_json(f"{env.HOME}/.eBlocBroker/whisperInfo.txt")
            kId = data["kId"]
        except:
            logging.error(f"[{WHERE(1)}] \n {traceback.format_exc()}")
            terminate()

        if not config.w3.geth.shh.hasKeyPair(kId):
            logging.error("E: Whisper node's private key of a key pair did not match with the given ID")
            logging.warning("Please first run: scripts/whisper_initialize.py")
            terminate()

    if not is_process_on("python.*[d]riverReceiver", "driverReceiver"):
        # running driver_cancel.py on the background
        # TODO: should be '0' to store log at a file and not print output
        config.whisper_state_receiver_process = subprocess.Popen(["python3", "whisperStateReceiver.py"])


def get_tx_status(output):
    logging.info(f"tx_hash={output}")
    receipt = config.w3.eth.waitForTransactionReceipt(output)
    logging.info("Transaction receipt mined: \n")
    # logging.info(pformat(receipt))
    pprint.pprint(dict(receipt))  # delete
    logging.info(f"Was transaction successful? => status={receipt['status']}")
    return receipt


def check_size_of_file_before_download(file_type, key=None):
    # TODO fill
    if int(file_type) == StorageID.IPFS.value or int(file_type) == StorageID.IPFS_MINILOCK.value:
        if not key:
            return False
    elif int(file_type) == StorageID.EUDAT.value:
        pass
    elif int(file_type) == StorageID.GDRIVE.value:
        pass
    return True


def terminate():
    """ Terminates Driver and all the dependent python programs to it."""
    logging.error(f"E: [{WHERE(1)}] terminate() function is called.")

    # following line is added, in case ./killall.sh does not work due to sudo
    # send the kill signal to all the process groups.
    if config.driver_cancel_process:
        os.killpg(os.getpgid(config.driver_cancel_process.pid), signal.SIGTERM)  # obtained from global variable

    if config.whisper_state_receiver_process:
        # obtained from global variable, # raise SystemExit("Program Exited")
        os.killpg(os.getpgid(config.whisper_state_receiver_process.pid), signal.SIGTERM)

    # kill all the dependent processes and exit
    output = subprocess.check_output(["bash", "killall.sh"]).decode("utf-8").rstrip()
    logging.info(output)
    sys.exit(1)


def _try(func):
    """Calls given function inside try/except

    Args:
        f: yield function

    Example called: _try(lambda: f())
    Returns status and output of the function
    """
    try:
        return func()
    except Exception:
        logging.error(f"[{WHERE(1)}] - {traceback.format_exc()}")
        raise


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
    return result_ipfs_hash


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
    try:
        success, output = run_command(cmd)
        result_ipfs_hash = _try(lambda: get_ipfs_parent_hash(output))
        return True, result_ipfs_hash
    except Exception:
        return False, None


def is_ipfs_hash_exists(ipfs_hash, attempt_count):
    logging.info(f"Attempting to check IPFS file {ipfs_hash}")
    for attempt in range(attempt_count):
        timeout_duration = "300"  # wait max 5 minutes
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


def ipfs_add(path, is_hidden=False):
    if os.path.isdir(path):
        if is_hidden:
            # include files that are hidden such as .git/. Only takes effect on recursive add
            cmd = ["ipfs", "add", "-r", "--hidden", "--quieter", "--progress", path]
        else:
            cmd = ["ipfs", "add", "-r", "--quieter", "--progress", path]
    elif os.path.isfile(path):
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
            time.sleep(5)  # wait 5 seconds for next retry to upload again
        else:  # success
            break
    else:  # failed all the attempts - abort
        sys.exit(1)

    return True, result_ipfs_hash


def calculate_folder_size(path) -> float:
    """Return the size of the given path in MB."""
    byte_size = 0
    p1 = subprocess.Popen(["du", "-sb", path], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["awk", "{print $1}"], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    byte_size = p2.communicate()[0].decode("utf-8").strip()
    return byte_to_mb(byte_size)


def log(text, color="", filename=None):
    if not filename:
        env = init_env()
        filename = f"{env.LOG_PATH}/transactions/provider.log"

    if color:
        print(colored(f"\033[1m{text}\033[0m", color))
    else:
        printc(text)
        # print(text, end="")  # no newline

    f = open(filename, "a")
    f.write(text)
    f.close()


def subprocess_call(cmd, attempt_count=1, print_flag=True):
    for count in range(attempt_count):
        try:
            return subprocess.check_output(cmd).decode("utf-8").strip()
        except Exception:
            if not count and print_flag:
                logging.error(f"[{WHERE(1)}] - {traceback.format_exc()}")

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
            _cmd = " ".join(cmd)
            logging.error(f"[{WHERE(1)}] - {traceback.format_exc()} command:\n {_cmd}")
            raise SystemExit


def run(cmd) -> str:
    try:
        return subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode("utf-8").strip()
    except Exception:
        _cmd = " ".join(cmd)
        logging.error(f"[{WHERE(1)}] \n {traceback.format_exc()} command:\n {_cmd}")
        raise


def run_command(cmd, my_env=None, is_exit_flag=False) -> Tuple[bool, str]:
    output = ""
    try:
        if my_env is None:
            output = subprocess.check_output(cmd).decode("utf-8").strip()
        else:
            output = subprocess.check_output(cmd, env=my_env).decode("utf-8").strip()
    except Exception:
        _cmd = " ".join(cmd)
        print(output)
        logging.error(f"[{WHERE(1)}] \n {traceback.format_exc()} command:\n {_cmd}")
        if is_exit_flag:
            terminate()
        return False, output
    return True, output


def silent_remove(path) -> bool:
    # link: https://stackoverflow.com/a/10840586/2402577
    try:
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            # deletes a directory and all its contents
            shutil.rmtree(path)
        else:
            return False

        logging.info(f"[{WHERE(1)}] - {path} is removed")
        return True
    except Exception:
        logging.error(f"[{WHERE(1)}] - {traceback.format_exc()}")
        return False


def remove_files(filename):
    if "*" in filename:
        for f in glob.glob(filename):
            if not silent_remove(f):
                return False
    else:
        if not silent_remove(filename):
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


def eblocbroker_function_call(func, attempt):
    for attempt in range(attempt):
        success, output = func()
        if success:
            return output
        else:
            logging.error(f"[{WHERE(1)}] E: {output}")
            if output == "notconnected":
                time.sleep(1)
            else:
                raise
    else:
        return output


def is_ipfs_hash_locally_cached(ipfs_hash) -> bool:
    """Run ipfs --offline refs -r or ipfs --offline block stat etc even if your normal daemon is running.
       With that you can check if something is available locally or no."""
    try:
        subprocess.check_output(["ipfs", "--offline", "block", "stat", ipfs_hash], stderr=subprocess.DEVNULL)
        return True
    except Exception:
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
        logging.warning(f"{name} is already running")
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
    env = init_env()
    port = str(env.RPC_PORT)
    port = insert_character(port, 1, "]")
    port = insert_character(port, 0, "[")
    return is_process_on(f"geth.*{port}", "Geth")


def preexec_function():
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def is_transaction_passed(tx_hash) -> bool:
    receipt = config.w3.eth.getTransactionReceipt(tx_hash)
    try:
        if receipt["status"] == 1:
            return True
    except:
        pass

    return False


def is_ipfs_running():
    """ Checks that does IPFS run on the background or not."""
    env = init_env()
    output = is_ipfs_on()
    if output:
        return True
    else:
        logging.error("E: IPFS does not work on the background.")
        logging.info("* Starting IPFS: nohup ipfs daemon --mount &")
        path = f"{env.LOG_PATH}/ipfs.out"
        with open(path, "w") as stdout:
            cmd = ["nohup", "ipfs", "daemon", "--mount"]
            subprocess.Popen(cmd, stdout=stdout, stderr=stdout, preexec_fn=os.setpgrp)
            logging.info(f"Writing into {path} is completed.")

        time.sleep(5)
        with open(path, "r") as content_file:
            logging.info(content_file.read())

        # ipfs mounted at: /ipfs
        output = subprocess.check_output(["sudo", "ipfs", "mount", "-f", "/ipfs"]).decode("utf-8").strip()
        logging.info(output)
        return is_ipfs_on()


def is_run_exists_in_tar(tar_path):
    try:
        logging.info(tar_path)
        output = (
            subprocess.check_output(["tar", "ztf", tar_path, "--wildcards", "*/run.sh"], stderr=subprocess.DEVNULL,)
            .decode("utf-8")
            .strip()
        )
        if output.count("/") == 1:  # main folder should contain the 'run.sh' file
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

    # tar produces different files each time: https://unix.stackexchange.com/a/438330/198423
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

    tar_hash = generate_md5sum(f"{base_name}.tar.gz")
    shutil.move(f"{base_name}.tar.gz", f"{tar_hash}.tar.gz")
    os.chdir(current_path)
    return tar_hash, f"{dir_path}/{tar_hash}.tar.gz"


def _sbatch_call(
    logged_job, requester_id, results_folder, results_folder_prev, dataTransferIn, source_code_hashes, job_info
):
    job_key = logged_job.args["jobKey"]
    index = logged_job.args["index"]
    main_cloud_storage_id = logged_job.args["cloudStorageID"][0]  # 0 indicated maps to sourceCode
    job_info = job_info[0]
    job_id = 0  # base job_id for them workflow

    # cmd: date --date=1 seconds +%b %d %k:%M:%S %Y
    date = (
        subprocess.check_output(["date", "--date=" + "1 seconds", "+%b %d %k:%M:%S %Y"], env={"LANG": "en_us_88591"},)
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
    # adding job_key info along with its cacheDuration into mongodb
    mongodb.add_item(
        job_key, source_code_hashes, requester_id, timestamp, main_cloud_storage_id, job_info,
    )

    # TODO: update as used_dataTransferIn value
    f = f"{results_folder_prev}/dataTransferIn.json"
    try:
        data = read_json(f)
        dataTransferIn = data["dataTransferIn"]
    except:
        data = {}
        data["dataTransferIn"] = dataTransferIn
        with open(f, "w") as outfile:
            json.dump(data, outfile)

    # logging.info(dataTransferIn)
    time.sleep(0.25)
    # seperator character is ;
    sbatch_file_path = f"{results_folder}/{job_key}*{index}*{main_cloud_storage_id}*{logged_job.blockNumber}.sh"
    copyfile(f"{results_folder}/run.sh", sbatch_file_path)

    job_core_num = str(job_info["core"][job_id])
    # client's requested seconds to run his/her job, 1 minute additional given
    execution_time_second = timedelta(seconds=int((job_info["executionDuration"][job_id] + 1) * 60))
    d = datetime(1, 1, 1) + execution_time_second
    time_limit = str(int(d.day) - 1) + "-" + str(d.hour) + ":" + str(d.minute)
    logging.info(f"time_limit={time_limit} | requested_core_num={job_core_num}")
    # give permission to user that will send jobs to Slurm.
    subprocess.check_output(["sudo", "chown", "-R", requester_id, results_folder])

    for attempt in range(10):
        try:
            # slurm submit job, Real mode -N is used. For Emulator-mode -N use 'sbatch -c'
            """ cmd:
            sudo su - $requester_id -c "cd $results_folder &&
            sbatch -c$job_core_num $results_folder/${job_key}*${index}*${main_cloud_storage_id}.sh --mail-type=ALL
            """
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
            time.sleep(1)  # wait 1 second for Slurm idle core to be updated
        except subprocess.CalledProcessError as e:
            logging.error(e.output.decode("utf-8").strip())
            success, output = run_command(
                ["sacctmgr", "remove", "user", "where", f"user={requester_id}", "--immediate",]
            )
            success, output = run_command(["sacctmgr", "add", "account", requester_id, "--immediate"])
            success, output = run_command(
                [
                    "sacctmgr",
                    "create",
                    "user",
                    requester_id,
                    f"defaultaccount={requester_id}",
                    "adminlevel=[None]",
                    "--immediate",
                ]
            )
        else:
            break
    else:
        sys.exit(1)

    slurm_job_id = job_id.split()[3]
    logging.info(f"slurm_job_id={slurm_job_id}")
    try:
        cmd = ["scontrol", "update", f"jobid={slurm_job_id}", f"TimeLimit={time_limit}"]
        subprocess.run(cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        logging.error(e.output.decode("utf-8").strip())

    if not slurm_job_id.isdigit():
        logging.error("E: Detects an error on the SLURM side. slurm_job_id is not a digit")
        return False

    return True


def is_dir(path) -> bool:
    if not os.path.isdir(path):
        logging.error(f"{path} folder does not exist.")
        return False
    return True


def remove_empty_files_and_folders(results_folder) -> None:
    """Remove empty files if exists"""
    p1 = subprocess.Popen(["find", results_folder, "-size", "0", "-print0"], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["xargs", "-0", "-r", "rm"], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    p2.communicate()

    # removes empty folders
    subprocess.run(["find", results_folder, "-type", "d", "-empty", "-delete"])
    p1 = subprocess.Popen(["find", results_folder, "-type", "d", "-empty", "-print0"], stdout=subprocess.PIPE,)
    p2 = subprocess.Popen(["xargs", "-0", "-r", "rmdir"], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    p2.communicate()
