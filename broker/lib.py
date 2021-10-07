#!/usr/bin/env python3

import glob
import os
import subprocess
import sys
import time
from multiprocessing import Process
from pprint import pprint
from threading import Thread
import broker.cfg as cfg
import broker.config as config
from broker._utils.tools import log, print_tb, print_trace
from broker.config import env, logging
from broker.utils import (
    Link,
    StorageID,
    _remove,
    byte_to_mb,
    is_process_on,
    mkdir,
    popen_communicate,
    question_yes_no,
    run,
)


def enum(*sequential, **named):
    """Set reverse mapping for the Enum.

    __ https://stackoverflow.com/a/1695250/2402577
    """
    enums = dict(zip(sequential, range(len(sequential))), **named)
    reverse = dict((value, key) for key, value in enums.items())
    enums["reverse_mapping"] = reverse
    return type("Enum", (), enums)


class State:
    """State code of the Slurm jobs, add keys into the hashmap.

    Hashmap keys:

        - SUBMITTED: Initial state.

        - PENDING: Indicates when a request is receieved by the provider.  The
          job is waiting for resource allocation.  It will eventually run.

        - RUNNING: The job currently is allocated to a node and isrunning.
          Corresponding data files are downloaded and verified.

        - REFUNDED: Indicates if job is refunded

        - CANCELLED: Job was explicitly cancelled by the requester or system
          administrator.  The job may or may not have been initiated.  Set by
          the requester.

        - COMPLETED: The job has completed successfully and deposit is paid to
          the provider.

        - TIMEOUT: Job terminated upon reaching its time limit.

    __ https://slurm.schedmd.com/squeue.html
    """

    code = {}
    code["SUBMITTED"] = 0
    code["PENDING"] = 1
    code["RUNNING"] = 2
    code["REFUNDED"] = 3
    code["CANCELLED"] = 4
    code["COMPLETED"] = 5
    code["TIMEOUT"] = 6
    code["COMPLETED_WAITING_ADDITIONAL_DATA_TRANSFER_OUT_DEPOSIT"] = 7  # TODO: check
    inv_code = {value: key for key, value in code.items()}


state = State()


def _connect_web3():
    if not cfg.w3:
        from broker.imports import connect_into_web3
        connect_into_web3()


def session_start_msg(slurm_user, block_number, pid):
    """Print message at the beginning of Driver process and connect into web3."""
    _connect_web3()
    if not env.PROVIDER_ID and cfg.w3:
        PROVIDER_ID = cfg.w3.toChecksumAddress(os.getenv("PROVIDER_ID"))
    else:
        PROVIDER_ID = env.PROVIDER_ID

    log(f"==> This Driver process has the PID {pid}")
    log(f"==> provider_address={PROVIDER_ID}")
    log(f"==> slurm_user={slurm_user}")
    log(f"==> block_number={block_number}")


def run_driver_cancel():
    """Run driver_cancel daemon on the background."""
    if not is_process_on("python.*[d]riverCancel", "driverCancel"):
        # Running driver_cancel.py on the background if it is not already
        config.driver_cancel_process = subprocess.Popen(["python3", "driver_cancel.py"])


def get_tx_status(tx_hash) -> str:
    """Return status of the transaction."""
    log(f"tx_hash={tx_hash}")
    tx_receipt = cfg.w3.eth.waitForTransactionReceipt(tx_hash)
    log("Transaction receipt is deployed:")
    pprint(dict(tx_receipt), depth=1)
    # for idx, _log in enumerate(receipt["logs"]):
    #     # All logs fried under the tx
    #     log(f"log {idx}", "blue")
    #     pprint(_log.__dict__)
    log("\n## Was transaction successful? ", filename=None)
    if tx_receipt["status"] == 1:
        log("Transaction is deployed", "bold green")
    else:
        raise Exception("E: Transaction is reverted")

    return tx_receipt


def check_size_of_file_before_download(file_type, key=None):
    """Check size of the file before downloading it."""
    if int(file_type) in (StorageID.IPFS, StorageID.IPFS_GPG):  # TODO: fill
        if not key:
            return False
    elif int(file_type) == StorageID.EUDAT:
        pass
    elif int(file_type) == StorageID.GDRIVE:
        pass
    return True


def calculate_folder_size(path, _type="mb") -> float:
    """Return the size of the given path in MB, bytes if wanted."""
    p1 = subprocess.Popen(["du", "-sb", path], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["awk", "{print $1}"], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()  # type: ignore
    byte_size = 0.0
    byte_size = float(p2.communicate()[0].decode("utf-8").strip())
    if _type == "bytes":
        return byte_size
    else:
        return byte_to_mb(byte_size)


def subprocess_call(cmd, attempt=1, print_flag=True):
    """Run subprocess."""
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
                log("Trying again...\nAttempts: ", "green", end="")
            log(f"{count}  ", "green", end="")
            time.sleep(0.25)


def run_stdout_to_file(cmd, path, mode="w") -> None:
    """Run command pipe output into give file."""
    p, output, error = popen_communicate(cmd, stdout_file=path, mode=mode)
    if p.returncode != 0 or (isinstance(error, str) and "error:" in error):
        _cmd = " ".join(cmd)
        log(f"\n{_cmd}", "red")
        logging.error(f"E: scontrol error\n{output}")
        raise

    logging.info(f"\nWriting into path is completed => {path}")
    run(["sed", "-i", "s/[ \t]*$//", path])  # remove trailing whitespaces with sed


def remove_files(filename) -> bool:
    """Remove give file path."""
    if "*" in filename:
        for f in glob.glob(filename):
            try:
                _remove(f)
            except:
                print_tb()
                return False
    else:
        try:
            _remove(filename)
        except:
            print_tb()
            return False

    return True


def echo_grep_awk(str_data, grep_str, column):
    """Echo grap awk.

    cmd: echo gdrive_info | grep _type | awk "{print $2}"
    """
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
                print_tb(e)
                raise e

    print_tb("E: eblocbroker_function_call completed all the attempts.")
    raise


def check_linked_data(path_from, path_to, folders_to_share=None, is_continue=False):
    """Generate folder as hard linked of the given folder paths or provider main folder.

    :param path_to: linked folders_to_share into into given path
    :param folders_to_share: if given, iterates all over the folders_to_share
    """
    mkdir(path_to)
    link = Link(path_from, path_to)
    link.link_folders(folders_to_share)
    log("")
    for key, value in link.data_map.items():
        log(f" * {key} ==> data_link/{value}")

    if not is_continue:
        print("")
        question_yes_no(
            "## Would you like to continue with linked folder path in your run.sh?\n"
            "If no, please update your run.sh file [Y/n]: "
        )

    for folder in folders_to_share:
        if not os.path.isdir(folder):
            log(f"E: {folder} path does not exist")
            sys.exit(1)


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


# def preexec_function():
#     signal.signal(signal.SIGINT, signal.SIG_IGN)
