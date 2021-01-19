#!/usr/bin/env python3

import datetime
import glob
import os
import pprint
import signal
import subprocess
import sys
import time
from multiprocessing import Process
from threading import Thread
from typing import Tuple, Union

import config
from config import env, logging
from utils import (
    Link,
    StorageID,
    _colorize_traceback,
    byte_to_mb,
    is_ipfs_on,
    is_process_on,
    log,
    mkdir,
    popen_communicate,
    print_trace,
    question_yes_no,
    read_json,
    run,
    silent_remove,
    terminate,
)


def enum(*sequential, **named):
    """Sets reverse mapping for the Enum.

    Helpful Links:
    - https://stackoverflow.com/a/1695250/2402577
    """
    enums = dict(zip(sequential, range(len(sequential))), **named)
    reverse = dict((value, key) for key, value in enums.items())
    enums["reverse_mapping"] = reverse
    return type("Enum", (), enums)


state_code = {}

# add keys to the hashmap # https://slurm.schedmd.com/squeue.html
state_code["SUBMITTED"] = 0  # initial state
# indicates when a request is receieved by the provider. The job is waiting
# for resource allocation. It will eventually run.
state_code["PENDING"] = 1
# The job currently is allocated to a node and is running. Corresponding data
# files are downloaded and verified.
state_code["RUNNING"] = 2
# indicates if job is refunded
state_code["REFUNDED"] = 3
# Job was explicitly cancelled by the requester or system administrator.
# The job may or may not have been initiated. Set by the requester
state_code["CANCELLED"] = 4
# The job has completed successfully and deposit is paid to the provider
state_code["COMPLETED"] = 5
# Job terminated upon reaching its time limit.
state_code["TIMEOUT"] = 6
state_code["COMPLETED_WAITING_ADDITIONAL_DATA_TRANSFER_OUT_DEPOSIT"] = 6

inv_state_code = {value: key for key, value in state_code.items()}


def _connect_web3():
    if not config.w3:
        from imports import connect_to_web3

        connect_to_web3()


def session_start_msg(slurm_user, block_number, pid, columns=104):
    _connect_web3()
    if not env.PROVIDER_ID and config.w3:
        PROVIDER_ID = config.w3.toChecksumAddress(os.getenv("PROVIDER_ID"))
    else:
        PROVIDER_ID = env.PROVIDER_ID

    _columns = int(int(columns) / 2 - 12)
    date_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    log(date_now + " " + "=" * (_columns - 16) + " provider session starts " + "=" * (_columns - 5), color="cyan")
    log(f"==> This Driver process has the PID {pid}")
    log(f"slurm_user={slurm_user} | provider_address={PROVIDER_ID} | block_number={block_number}", color="blue")


def run_driver_cancel():
    """Runs driver_cancel daemon on the background."""
    if not is_process_on("python.*[d]riverCancel", "driverCancel"):
        # running driver_cancel.py on the background if it is not already
        config.driver_cancel_process = subprocess.Popen(["python3", "driver_cancel.py"])


def run_whisper_state_receiver():
    """Runs driverReceiver daemon on the background."""
    if not os.path.isfile(env.WHISPER_INFO):
        # first time running
        logging.warning(f"Please run:\n{env.EBLOCPATH}/whisper/initialize.py")
        terminate(msg="", is_traceback=False)
    else:
        try:
            data = read_json(env.WHISPER_INFO)
            key_id = data["key_id"]
        except:
            _colorize_traceback()
            terminate()

        if not config.w3.geth.shh.hasKeyPair(key_id):
            logging.warning("Please first run: python_scripts/whisper_initialize.py")
            terminate("E: Whisper node's private key of a key pair did not match with the given ID")

    if not is_process_on("python.*[d]riverReceiver", "driverReceiver"):
        # running driver_cancel.py on the background
        # TODO: should be '0' to store log at a file and not print output
        config.whisper_state_receiver_process = subprocess.Popen(["python3", "whisper/state_receiver.py"])


def get_tx_status(tx_hash) -> str:
    log(f"tx_hash={tx_hash}")
    tx_receipt = config.w3.eth.waitForTransactionReceipt(tx_hash)
    logging.info("Transaction receipt is mined:")
    pprint.pprint(dict(tx_receipt), depth=1)
    # logging.info(pformat(receipt))
    # log("")
    # for idx, _log in enumerate(receipt["logs"]):
    #     # All logs fried under the tx
    #     log(f"log {idx}", "blue")
    #     pprint.pprint(_log.__dict__)

    log("\n#> Was transaction successful? ", color="white", filename=None)
    if tx_receipt["status"] == 1:
        log("Transaction is deployed", "green")
    else:
        log("E: Transaction is reverted", "red")
    return tx_receipt


def check_size_of_file_before_download(file_type, key=None):
    # TODO: fill
    if int(file_type) in (StorageID.IPFS, StorageID.IPFS_GPG):
        if not key:
            return False
    elif int(file_type) == StorageID.EUDAT:
        pass
    elif int(file_type) == StorageID.GDRIVE:
        pass
    return True


def calculate_folder_size(path, _type="mb") -> float:
    """Return the size of the given path in MB, bytes if wanted"""
    byte_size = 0
    p1 = subprocess.Popen(["du", "-sb", path], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["awk", "{print $1}"], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()  # type: ignore
    byte_size = p2.communicate()[0].decode("utf-8").strip()
    if _type == "bytes":
        return byte_size
    else:
        return byte_to_mb(byte_size)


def subprocess_call(cmd, attempt=1, print_flag=True):
    cmd = list(map(str, cmd))  # always should be type: str
    for count in range(attempt):
        try:
            return subprocess.check_output(cmd).decode("utf-8").strip()
        except Exception:
            if not count and print_flag:
                print_trace(cmd)

            if count + 1 == attempt:
                log("")
                raise SystemExit

            if count == 0:
                log("Trying again...\nAttempts: ", color="green", end="")
            log(f"{count}  ", end="", color="green")
            time.sleep(0.25)


def run_stdout_to_file(cmd, path) -> None:
    p, output, error = popen_communicate(cmd, stdout_file=path)
    if p.returncode != 0 or (isinstance(error, str) and "error:" in error):
        _cmd = " ".join(cmd)
        log(f"\n{_cmd}", color="red")
        logging.error(f"E: scontrol error\n{output}")
        raise
    logging.info(f"\nWriting into path is completed => {path}")
    run(["sed", "-i", "s/[ \t]*$//", path])  # removes trailing whitespaces with sed


def run_command(cmd, my_env=None) -> Tuple[bool, str]:
    cmd = list(map(str, cmd))  # all items should be string
    output = ""
    try:
        if my_env is None:
            output = subprocess.check_output(cmd).decode("utf-8").strip()
        else:
            output = subprocess.check_output(cmd, env=my_env).decode("utf-8").strip()
    except Exception:
        print(output)
        print_trace(cmd)
        return False, output
    return True, output


def remove_files(filename) -> bool:
    if "*" in filename:
        for f in glob.glob(filename):
            try:
                silent_remove(f)
            except:
                _colorize_traceback()
                return False
    else:
        try:
            silent_remove(filename)
        except:
            _colorize_traceback()
            return False

    return True


def echo_grep_awk(str_data, grep_str, column):
    """cmd: echo gdrive_info | grep _type | awk \'{print $2}\'"""
    p1 = subprocess.Popen(["echo", str_data], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["grep", grep_str], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    p3 = subprocess.Popen(["awk", "{print $" + column + "}"], stdin=p2.stdout, stdout=subprocess.PIPE)
    p2.stdout.close()
    return p3.communicate()[0].decode("utf-8").strip()


def eblocbroker_function_call(func, attempt):
    for _attempt in range(attempt):
        try:
            return func()
        except Exception as e:
            if type(e).__name__ == "Web3NotConnected":
                time.sleep(1)
            else:
                _colorize_traceback()
                raise
    raise


def preexec_function():
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def is_ipfs_running():
    """Checks that does IPFS run on the background or not."""
    if is_ipfs_on():
        return True

    log("E: IPFS does not work on the background", "blue")
    log("## Starting IPFS daemon on the background", "blue")
    while True:
        output = run(["python3", f"{env.EBLOCPATH}/daemons/ipfs.py"])
        log(output, "blue")
        time.sleep(1)
        if is_ipfs_on():
            break
        else:
            with open(env.IPFS_LOG, "r") as content_file:
                logging.info(content_file.read())
        time.sleep(1)
    return is_ipfs_on()


def check_linked_data(path_from, path_to, folders=None, is_continue=False):
    """Generates folder as hard linked of the given folder paths or provider main folder.

    :param path_to: linked folders into into given path
    :param folders: if given, iterates all over the folders
    """
    mkdir(path_to)
    link = Link(path_from, path_to)
    link.link_folders(folders)
    log("")
    for key, value in link.data_map.items():
        log("*", color="blue", end="")
        print(f" {key} ==> data_link/{value}")

    if not is_continue:
        question_yes_no(
            "\n## Would you like to continue with linked folder path in your run.sh?\n"
            "If yes, please update your run.sh file [Y/n]: "
        )


def is_dir(path) -> bool:
    if not os.path.isdir(path):
        logging.error(f"==> {path} folder does not exist")
        return False
    return True


def run_storage_thread(storage_class):
    # consider giving the thread a name (add name=...), then you could
    # use ThreadFilter(threadname=...) to select on all messages with that name
    # The thread name does not have to be unique.
    storage_thread = Thread(target=storage_class.run)
    storage_thread.name = storage_class.thread_name

    # This thread dies when main thread (only non-daemon thread) exits
    storage_thread.daemon = True
    log(f"==> thread_log_path={storage_class.drivers_log_path}")
    storage_thread.start()
    try:
        storage_thread.join()  # waits until the job is completed
    except (KeyboardInterrupt, SystemExit):
        sys.stdout.flush()
        sys.exit(1)


def run_storage_process(storage_class):
    storage_process = Process(target=storage_class.run)
    storage_process.start()
    try:
        storage_process.join()  # waits until the job is completed
    except (KeyboardInterrupt, SystemExit):
        storage_process.terminate()
        sys.exit(1)
