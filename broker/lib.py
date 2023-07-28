#!/usr/bin/env python3

import glob
import os
import subprocess
import sys
import time
import traceback
from multiprocessing import Process
from os.path import exists
from threading import Thread

from broker import cfg, config
from broker._utils._log import WHERE, br
from broker._utils.tools import _remove, gdrive_about_user, is_process_on, log, mkdir, print_tb
from broker.config import env
from broker.errors import Terminate
from broker.utils import byte_to_mb, popen_communicate, run


class JobType:
    TYPE = {
        "BEGIN": 0,
        "BETWEEN": 1,
        "FINAL": 2,
        "SINGLE": 3,
    }
    inv_code = {value: key for key, value in TYPE.items()}


class State:
    """Set state code of slurm jobs and add their keys link in the hashmap.

    * Hashmap keys:
    - SUBMITTED: Initial state of the job.

    - PENDING: Indicates when a request is receieved by the provider. The
      job is waiting for resource allocation. It will eventually run.

    - RUNNING: The job currently is allocated to a node and is running.
      Corresponding data files are downloaded and verified.

    - REFUNDED: The ob has been refunded.

    - CANCELLED: The job was explicitly cancelled by the requester or system
      administrator.  The job may or may not have been initiated.  Set by
     the requester.

    - COMPLETED: The job has completed successfully and deposit is paid to
      the provider.

    - TIMEOUT: The job has terminated upon reaching its time limit.

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
        "COMPLETED_AND_WAITING_ADDITIONAL_TRANSFER_OUT_DEPOSIT": 7,  # TODO: check
    }
    inv_code = {value: key for key, value in code.items()}


state = State()
JOB = JobType()


def enum(*sequential, **named):
    """Set reverse map dict for the Enum.

    __ https://stackoverflow.com/a/1695250/2402577
    """
    enums = dict(zip(sequential, range(len(sequential))), **named)
    enums["reverse_map"] = dict((value, key) for key, value in enums.items())
    return type("Enum", (), enums)


def session_start_msg(bn):
    """Print message at the beginning of the driver process and connect into Web3."""
    PROVIDER_ID = cfg.ZERO_ADDRESS
    if env.PROVIDER_ID:
        PROVIDER_ID = env.PROVIDER_ID
    elif cfg.w3:
        PROVIDER_ID = cfg.w3.toChecksumAddress(os.getenv("PROVIDER_ID"))

    log(f"* left_of_block_number={bn}")
    log(f"** latest_block_number={cfg.Ebb.get_block_number()}")
    if PROVIDER_ID == cfg.ZERO_ADDRESS:
        raise Terminate(f"provider_address={cfg.ZERO_ADDRESS} is invalid")


def calculate_size(path, _type="MB") -> float:
    """Return the size of the given path in MB, bytes if wanted."""
    p1 = subprocess.Popen(["du", "-sb", path], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["awk", "{print $1}"], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()  # type: ignore
    output = p2.communicate()[0].decode("utf-8").strip()
    byte_size = float(output)
    if _type == "bytes":
        return byte_size

    return byte_to_mb(byte_size)


def subprocess_call(cmd, attempt=1, sleep_time=1):
    """Run the subprocess."""
    error_msg = ""
    cmd = list(map(str, cmd))  # type of the cmd should be `str`
    for count in range(attempt):
        try:
            p, output, error_msg = popen_communicate(cmd)
            if p.returncode != 0:
                if count == 0:
                    _cmd = " ".join(cmd)
                    log(f"\n$ {_cmd}", "bold red")
                    log(f"{error_msg} ", "bold", end="")
                    log(f"WHERE={WHERE()}")

                if attempt > 1 and count + 1 != attempt:
                    log(f"{br(f'attempt={count}')} ", end="")
                    time.sleep(sleep_time)
            else:
                return output
        except Exception as e:
            # __ https://stackoverflow.com/a/1156048/2402577
            for line in traceback.format_stack():
                log(line.strip())

            raise e

    raise Exception(error_msg)


def run_stdout_to_file(cmd, path, mode="w") -> None:
    """Run command pipe output into the given file."""
    p, output, error = popen_communicate(cmd, stdout_fn=path, mode=mode)
    if p.returncode != 0 or (isinstance(error, str) and "error:" in error):
        _cmd = " ".join(cmd)
        log(f"\n{_cmd}", "red")
        raise Exception(f"scontrol error:\n{output}")

    # log(f"==> writing into path({path})  [  OK  ]")
    run(["sed", "-i", "s/[ \t]*$//", path])  # remove trailing whitespaces using sed


def remove_files(fn) -> bool:
    """Remove given file path."""
    if "*" in fn:
        for f in glob.glob(fn):
            try:
                _remove(f)
            except Exception as e:
                print_tb(e)
                return False
    else:
        try:
            _remove(fn)
        except Exception as e:
            print_tb(e)
            return False

    return True


def echo_grep_awk(str_data, grep_str, column):
    """Echo grep awk.

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
        except Exception as e:
            log(f"E: {e} {func}")
            log("sleep 15 seconds, will try again...")
            time.sleep(15)

    raise Exception("eblocbroker_function_call completed all the attempts  [  ABORT  ]")


def run_storage_thread(storage_class):
    """Run the storage driver as thread.

    Consider giving the thread a name (add name=...), then you could
    use ThreadFilter(threadname=...) to select on all messages with that name
    The thread name does not have to be unique.
    """
    storage_thread = Thread(target=storage_class.run)
    storage_thread.name = storage_class.thread_name
    # This thread dies when main thread (only non-daemon thread) exits
    storage_thread.daemon = True
    log(f"==> thread_log_fn={storage_class.drivers_log_path}")
    storage_thread.start()
    if cfg.IS_THREAD_JOIN:
        try:
            storage_thread.join()  # waits until the job is completed
        except (KeyboardInterrupt, SystemExit):
            sys.stdout.flush()
            sys.exit(1)


def run_storage_process(storage_class):
    try:
        storage_process = Process(target=storage_class.run)
        storage_process.start()
        storage_process.join()  # waits until the job completes
    except (KeyboardInterrupt, SystemExit):
        storage_process.terminate()
        # termination is done on the thread base
        sys.exit(1)


def run_driver_cancel():
    """Run driver_cancel daemon on the background."""
    if not is_process_on("python.*[d]river_cancel", "driver_cancel"):
        config.driver_cancel_process = subprocess.Popen(["python3", "driver_cancel.py"])


def pre_check():
    folders = [
        env.LOG_DIR / "links",
        env.LOG_DIR / "private",
        env.LOG_DIR / "transactions",
        env.LOG_DIR / "drivers_output",
        env.LOG_DIR / "end_code_output",
    ]
    for folder in folders:
        mkdir(env.LOG_DIR / folder)

    if env.IS_GDRIVE_USE:
        output = gdrive_about_user()
        if "@gmail.com" in output and output != env.GMAIL:
            raise Terminate("User at 'gdrive about' does not match with the registered gmail.")

    if not exists(env.PROGRAM_PATH / "slurm_mail_prog.sh"):
        msg = f"The `slurm_mail_prog.sh` scripts is not located in {env.PROGRAM_PATH}"
        raise Terminate(msg)


# def preexec_function():
#     signal.signal(signal.SIGINT, signal.SIG_IGN)
