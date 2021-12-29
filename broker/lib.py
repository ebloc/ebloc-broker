#!/usr/bin/env python3

import glob
import traceback

# import hashlib
import os
import subprocess
import sys
import time
from multiprocessing import Process
from threading import Thread

from broker import cfg, config
from broker._utils._log import br
from broker._utils.tools import _remove, is_process_on, log, print_tb
from broker.config import env, logging
from broker.errors import Web3NotConnected
from broker.utils import WHERE, byte_to_mb, popen_communicate, run


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

        - PENDING: Indicates when a request is receieved by the provider. The
          job is waiting for resource allocation.  It will eventually run.

        - RUNNING: The job currently is allocated to a node and isrunning.
          Corresponding data files are downloaded and verified.

        - REFUNDED: Indicates if job is refunded.

        - CANCELLED: Job was explicitly cancelled by the requester or system
          administrator.  The job may or may not have been initiated.  Set by
          the requester.

        - COMPLETED: The job has completed successfully and deposit is paid to
          the provider.

        - TIMEOUT: Job terminated upon reaching its time limit.

    __ https://slurm.schedmd.com/squeue.html
    """

    code = {
        "SUBMITTED": 0,
        "PENDING": 1,
        "RUNNING": 2,
        "REFUNDED": 3,
        "CANCELLED": 4,
        "COMPLETED": 5,
        "TIMEOUT": 6,
        "COMPLETED_WAITING_ADDITIONAL_DATA_TRANSFER_OUT_DEPOSIT": 7,  # TODO: check
    }
    inv_code = {value: key for key, value in code.items()}


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

    log(f"==> Driver process has the PID={pid}")
    log(f"==> provider_address={PROVIDER_ID}")
    log(f"==> slurm_user={slurm_user}")
    log(f"==> left_of_block_number={block_number}")
    log(f"==> latest__block_number={cfg.Ebb.get_block_number()}")


def run_driver_cancel():
    """Run driver_cancel daemon on the background."""
    if not is_process_on("python.*[d]river_cancel", "driver_cancel"):
        # Running driver_cancel.py on the background if it is not already
        config.driver_cancel_process = subprocess.Popen(["python3", "driver_cancel.py"])


def calculate_size(path, _type="MB") -> float:
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


def subprocess_call(cmd, attempt=1, sleep_time=1):
    """Run subprocess."""
    cmd = list(map(str, cmd))  # always should be type: str
    for count in range(attempt):
        try:
            p, output, error_msg = popen_communicate(cmd)
            if p.returncode != 0:
                if count == 0:
                    _cmd = " ".join(cmd)
                    log(f"\n$ {_cmd}", "bold red")
                    log(f"{error_msg} ", "bold", end="")
                    log(WHERE())

                if count + 1 == attempt:
                    raise Exception(error_msg)

                if attempt > 1:
                    log(f"{br(f'attempt={count}')} ", end="")
                    time.sleep(sleep_time)
            else:
                return output
        except Exception as e:
            # https://stackoverflow.com/a/1156048/2402577
            for line in traceback.format_stack():
                log(line.strip())

            raise e


def run_stdout_to_file(cmd, path, mode="w") -> None:
    """Run command pipe output into give file."""
    p, output, error = popen_communicate(cmd, stdout_file=path, mode=mode)
    if p.returncode != 0 or (isinstance(error, str) and "error:" in error):
        _cmd = " ".join(cmd)
        log(f"\n{_cmd}", "red")
        log(f"E: scontrol error\n{output}")
        raise

    # log(f"## writing into path({path}) is completed")
    run(["sed", "-i", "s/[ \t]*$//", path])  # remove trailing whitespaces with sed


def remove_files(filename) -> bool:
    """Remove given file path."""
    if "*" in filename:
        for f in glob.glob(filename):
            try:
                _remove(f)
            except Exception as e:
                print_tb(str(e))
                return False
    else:
        try:
            _remove(filename)
        except Exception as e:
            print_tb(str(e))
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


def eblocbroker_function_call(func, max_retries):
    for _ in range(max_retries):
        try:
            return func()
        except Web3NotConnected:
            time.sleep(1)
        except Exception as e:
            print_tb(e)
            raise e

    raise Exception("E: eblocbroker_function_call completed all the attempts.")


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


# from broker.utils StorageID
#
# def check_size_of_file_before_download(file_type, key=None):
#     """Check size of the file before downloading it."""
#     # TODO: fill
#     if int(file_type) in (StorageID.IPFS, StorageID.IPFS_GPG):
#         if not key:
#             return False
#     elif int(file_type) == StorageID.EUDAT:
#         pass
#     elif int(file_type) == StorageID.GDRIVE:
#         pass
#     return True


# def preexec_function():
#     signal.signal(signal.SIGINT, signal.SIG_IGN)

state = State()
