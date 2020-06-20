#!/usr/bin/env python3

import glob
import os
import pprint
import shutil
import signal
import subprocess
import sys
import time
from multiprocessing import Process
from threading import Thread
from typing import Tuple

import config
from config import env, logging
from startup import bp  # noqa: F401
from utils import (
    WHERE,
    Link,
    StorageID,
    _colorize_traceback,
    byte_to_mb,
    create_dir,
    generate_md5sum,
    is_ipfs_on,
    is_process_on,
    log,
    print_trace,
    printc,
    question_yes_no,
    read_json,
    run,
    terminate,
)


def enum(*sequential, **named):
    """Sets reverse mapping for the Enum.

    helpful: https://stackoverflow.com/a/1695250/2402577
    """
    enums = dict(zip(sequential, range(len(sequential))), **named)
    reverse = dict((value, key) for key, value in enums.items())
    enums["reverse_mapping"] = reverse
    return type("Enum", (), enums)


if not config.w3:
    from imports import connect_to_web3

    connect_to_web3()

PROVIDER_ID = config.w3.toChecksumAddress(os.getenv("PROVIDER_ID"))

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


def session_start_msg(slurm_user, block_number, columns=104):
    _columns = int(int(columns) / 2 - 12)
    log("=" * _columns + " provider session starts " + "=" * _columns, "cyan")
    printc(f"slurm_user={slurm_user} | provider_address={PROVIDER_ID} | block_number={block_number}", "blue")


def run_driver_cancel():
    """Runs driver_cancel daemon on the background."""
    if not is_process_on("python.*[d]riverCancel", "driverCancel"):
        # running driver_cancel.py on the background if it is not already
        config.driver_cancel_process = subprocess.Popen(["python3", "driver_cancel.py"])


def run_whisper_state_receiver():
    """Runs driverReceiver daemon on the background."""
    if not os.path.isfile(env.WHISPER_INFO):
        # first time running
        logging.warning(f"Run: {env.EBLOCPATH}/whisper/initialize.py")
        terminate()
    else:
        try:
            data = read_json(env.WHISPER_INFO)
            kId = data["kId"]
        except:
            _colorize_traceback()
            terminate()

        if not config.w3.geth.shh.hasKeyPair(kId):
            logging.error("E: Whisper node's private key of a key pair did not match with the given ID")
            logging.warning("Please first run: python_scripts/whisper_initialize.py")
            terminate()

    if not is_process_on("python.*[d]riverReceiver", "driverReceiver"):
        # running driver_cancel.py on the background
        # TODO: should be '0' to store log at a file and not print output
        config.whisper_state_receiver_process = subprocess.Popen(["python3", "whisper/state_receiver.py"])


def get_tx_status(tx_hash):
    if not tx_hash:
        log(f"tx_hash={tx_hash}")
        return tx_hash

    log(f"tx_hash={tx_hash}")
    receipt = config.w3.eth.waitForTransactionReceipt(tx_hash)
    logging.info("Transaction receipt mined:")
    # logging.info(pformat(receipt))
    pprint.pprint(dict(receipt))  # delete
    log("#> Was transaction successful?")
    if receipt["status"] == 1:
        log("Transaction is deployed", "green")
    else:
        log("E: Transaction is reverted", "red")

    return receipt


def check_size_of_file_before_download(file_type, key=None):
    # TODO fill
    if int(file_type) in (StorageID.IPFS, StorageID.IPFS_GPG):
        if not key:
            return False
    elif int(file_type) == StorageID.EUDAT:
        pass
    elif int(file_type) == StorageID.GDRIVE:
        pass
    return True


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
        _colorize_traceback()
        raise


def calculate_folder_size(path) -> float:
    """Return the size of the given path in MB."""
    byte_size = 0
    p1 = subprocess.Popen(["du", "-sb", path], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["awk", "{print $1}"], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    byte_size = p2.communicate()[0].decode("utf-8").strip()
    return byte_to_mb(byte_size)


def subprocess_call(cmd, attempt=1, print_flag=True):
    for count in range(attempt):
        try:
            return subprocess.check_output(cmd).decode("utf-8").strip()
        except Exception:
            if not count and print_flag:
                print_trace(cmd)

            if count + 1 == attempt:
                raise SystemExit

            logging.info(f"try={count}")
            time.sleep(0.1)


def run_stdout_to_file(cmd, path) -> None:
    with open(path, "w") as stdout:
        try:
            subprocess.Popen(cmd, stdout=stdout)
            logging.info(f"Writing into path is completed => {path}")
        except Exception:
            print_trace(cmd)
            raise SystemExit


def run_command(cmd, my_env=None) -> Tuple[bool, str]:
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


def silent_remove(path) -> bool:
    """Removes file or folders based on the file type.

    doc:
    - https://stackoverflow.com/a/10840586/2402577
    """

    try:
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            # deletes a directory and all its contents
            shutil.rmtree(path)
        else:
            return False

        logging.info(f"[{WHERE(1)}]\n{path} is removed")
        return True
    except Exception:
        _colorize_traceback()
        return False


def remove_files(filename) -> bool:
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
    log("#> Starting IPFS daemon on the background", "blue")
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


def check_linked_data(path_from, path_to, folders=None, force_continue=False):
    """Generates folder as hard linked of the given folder paths or provider main folder.

    :param path_to: linked folders into into given path
    :param folders: if given, iterate over all folders
    """
    create_dir(path_to)
    link = Link(path_from, path_to)
    link.link_folders(folders)

    for key, value in link.data_map.items():
        print(f"{key} => data_link/{value}")

    if force_continue:
        return

    question_yes_no("#> Would you like to continue with linked folder path in your run.sh? [Y/n]: ")


# TODO: carry into utils
def compress_folder(folder_to_share):
    """Compress folder using tar
    - Note that to get fully reproducible tarballs, you should also impose the sort order used by tar:

    Helpful links:
    - https://unix.stackexchange.com/a/438330/198423,
    - https://unix.stackexchange.com/questions/580685/why-does-the-pigz-produce-a-different-md5sum
    """
    current_path = os.getcwd()
    base_name = os.path.basename(folder_to_share)
    dir_path = os.path.dirname(folder_to_share)
    os.chdir(dir_path)

    # tar produces different files each time: https://unix.stackexchange.com/a/438330/198423
    """cmd:
    find . -print0 | LC_ALL=C sort -z | \
    PIGZ=-n tar -Ipigz --mode=a+rwX --owner=0 --group=0 --numeric-owner --absolute-names --no-recursion --null -T - -zcvf $tar_hash.tar.gz
    """
    p1 = subprocess.Popen(["find", base_name, "-print0"], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["sort", "-z"], stdin=p1.stdout, stdout=subprocess.PIPE, env={"LC_ALL": "C"})
    p1.stdout.close()
    p3 = subprocess.Popen(
        [
            "tar",
            "-Ipigz",
            "--mode=a+rwX",
            "--owner=0",
            "--group=0",
            "--numeric-owner",
            "--absolute-names",
            "--no-recursion",
            "--null",
            "-T",
            "-",
            "-cvf",
            f"{base_name}.tar.gz",
        ],
        stdin=p2.stdout,
        stdout=subprocess.PIPE,
        env={"PIGZ": "-n"},  # GZIP
    )
    p2.stdout.close()
    p3.communicate()

    tar_hash = generate_md5sum(f"{base_name}.tar.gz")
    tar_file = f"{tar_hash}.tar.gz"
    shutil.move(f"{base_name}.tar.gz", tar_file)
    log(f"Created tar file={dir_path}/{tar_file}")
    os.chdir(current_path)
    return tar_hash, f"{dir_path}/{tar_file}"


def is_dir(path) -> bool:
    if not os.path.isdir(path):
        logging.error(f"{path} folder does not exist")
        return False
    return True


def run_storage_thread(storage_class):
    # consider giving the thread a name (add name=...), then you could
    # use ThreadFilter(threadname=...) to select on all messages with that name
    # The thread name does not have to be unique.
    storage_thread = Thread(target=storage_class.run)
    storage_thread.name = storage_class.thread_name

    # This thread dies when main thread (only non-daemon thread) exits.
    storage_thread.daemon = True
    log("==> ", "blue", None, is_new_line=False)
    log(f"thread_log_path={storage_class.drivers_log_path}")
    storage_thread.start()
    try:
        storage_thread.join()  # waits until the job is completed
    except (KeyboardInterrupt, SystemExit):
        sys.stdout.flush()
        sys.exit(1)  # KeyboardInterrupt


def run_storage_process(storage_class):
    storage_process = Process(target=storage_class.run)
    storage_process.start()
    try:
        storage_process.join()  # waits until the job is completed
    except (KeyboardInterrupt, SystemExit):
        storage_process.terminate()
        sys.exit(1)  # KeyboardInterrupt
