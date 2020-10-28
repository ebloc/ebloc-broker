#!/usr/bin/env python3

import binascii
import errno
import hashlib
import json
import ntpath
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
import traceback
from contextlib import suppress
from enum import IntEnum
from subprocess import PIPE, STDOUT, CalledProcessError, Popen, check_output

import base58
from pygments import formatters, highlight, lexers
from termcolor import colored

import config
from _utils._getch import _Getch
from config import env, logging

Qm = b"\x12 "
empty_bytes32 = b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
zero_bytes32 = "0x00"

yes = set(["yes", "y", "ye", "ys"])
no = set(["no", "n"])
log_files = {}


class BashCommandsException(Exception):
    def __init__(self, returncode, output, error_msg):
        self.returncode = returncode
        self.output = output
        self.error_msg = error_msg
        Exception.__init__('Error in the executed command')


class BaseEnum(IntEnum):
    def __str__(self):
        return str(self.value)

    def __int__(self):
        return int(self.value)

    def __eq__(self, other):
        return int(self.value) == other


class CacheType(BaseEnum):
    PUBLIC = 0
    PRIVATE = 1


class StorageID(BaseEnum):
    IPFS = 0
    EUDAT = 1
    IPFS_GPG = 2
    GITHUB = 3
    GDRIVE = 4
    NONE = 5


class COLOR:
    BOLD = "\033[1m"
    PURPLE = "\033[95m"
    BLUE = "\033[94m"
    END = "\033[0m"


def print_warning(msg):
    log("Warning: ", "yellow", None, is_new_line=True)
    log(msg)


def print_arrow(color="white"):
    log("==> ", color, None, is_new_line=False)


def extract_gzip(filename):
    run(["gunzip", "--force", filename])


def untar(tar_file, extract_to):
    """ untar give tar file
    umask can be ignored by using the -p (--preserve) option
        --no-overwrite-dir: preserve metadata of existing directories

    tar interprets the next argument after -f as the file name of the tar file.
    Put the p before the f:
    """
    filename = os.path.basename(tar_file)
    accept_files = [".git", filename]
    if not is_dir_empty(extract_to):
        for name in os.listdir(extract_to):
            # if tar itself already exist inside the same directory along with
            # `.git` file
            if name not in accept_files:
                log(f"{tar_file} is already extracted into {extract_to}")
                return

    cmd = ["tar", "-xvpf", tar_file, "-C", extract_to, "--no-overwrite-dir", "--strip", "1"]
    run(cmd)


def is_internet_on(host="8.8.8.8", port=53, timeout=3) -> bool:
    """ Host: 8.8.8.8 (google-public-dns-a.google.com)
    OpenPort: 53/tcp
    Service: domain (DNS/TCP)
    doc: https://stackoverflow.com/a/33117579/2402577
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error as ex:
        print(ex)
        return False


def sleep_timer(sleep_duration):
    log(f"Sleeping for {sleep_duration} seconds. Called from {[WHERE(1)]}", "blue")
    for remaining in range(sleep_duration, 0, -1):
        sys.stdout.write("\r")
        sys.stdout.write("{:1d} seconds remaining...".format(remaining))
        sys.stdout.flush()
        time.sleep(1)
    sys.stdout.write("\rSleeping is done!                               \n")


def remove_ansi_escape_sequence(string):
    # https://stackoverflow.com/questions/14693701/how-can-i-remove-the-ansi-escape-sequences-from-a-string-in-python
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", string)


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


def run(cmd, is_print_trace=True) -> str:
    cmd = list(map(str, cmd))  # all items should be str
    try:
        return check_output(cmd, stderr=STDOUT).decode("utf-8").strip()
    except Exception as e:
        if is_print_trace:
            print_trace(cmd, back=2, exc=e.output.decode("utf-8"))
            _colorize_traceback()
        raise e


def run_with_output(cmd):
    # https://stackoverflow.com/questions/4417546/constantly-print-subprocess-output-while-process-is-running
    cmd = list(map(str, cmd))  # all items should be str
    ret = ""
    with Popen(cmd, stdout=PIPE, bufsize=1, universal_newlines=True) as p:
        for line in p.stdout:
            ret += line
            print(line, end='')  # process line here
            return line.strip()
    if p.returncode != 0:
        raise CalledProcessError(p.returncode, p.args)


def popen_communicate(cmd, stdout_file=None, mode="w"):
    """Acts similir to lib.run(cmd) but also returns the output message captures on
    during the run stdout_file is not None in case of nohup process writes its
    results into a file
    """
    cmd = list(map(str, cmd))  # all items should be str
    if stdout_file is None:
        p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    else:
        with open(stdout_file, mode) as outfile:
            # output written into file, error will be returned
            p = Popen(cmd, stdout=outfile, stderr=PIPE, universal_newlines=True)
            output, error = p.communicate()
            p.wait()
            return p, output, error

    output, error = p.communicate()
    output = output.strip().decode("utf-8")
    error = error.decode("utf-8")
    return p, output, error


def is_transaction_passed(tx_hash) -> bool:
    receipt = config.w3.eth.getTransactionReceipt(tx_hash)
    try:
        if receipt["status"] == 1:
            return True
    except:
        pass
    return False


def insert_character(string, index, char) -> str:
    return string[:index] + char + string[index:]


def _colorize_traceback(string=None):
    """Logs the traceback."""
    tb_text = "".join(traceback.format_exc())
    lexer = lexers.get_lexer_by_name("pytb", stripall=True)
    # to check: print $terminfo[colors]
    formatter = formatters.get_formatter_by_name("terminal")
    tb_colored = highlight(tb_text, lexer, formatter)
    if not string:
        log(f"{[WHERE(1)]} ", "blue", None, is_new_line=False)
    else:
        log(f"[{WHERE(1)} {string}] ", "blue", None, is_new_line=False)
    log(tb_colored)


def get_time():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def bytes32_to_string(bytes_array):
    return base58.b58encode(bytes_array).decode("utf-8")


def string_to_bytes32(hash_str: str):
    """Convert string into  bytes array."""
    bytes_array = base58.b58decode(hash_str)
    return binascii.hexlify(bytes_array).decode("utf-8")


def bytes32_to_ipfs(bytes_array):
    """Convert bytes_array into IPFS hash format."""
    if isinstance(bytes_array, bytes):
        merge = Qm + bytes_array
        return base58.b58encode(merge).decode("utf-8")
    else:
        logging.info(f"{isinstance} is not a bytes instance")
    return bytes_array


def _ipfs_to_bytes32(hash_str: str):
    """Ipfs hash is converted into bytes32 format."""
    bytes_array = base58.b58decode(hash_str)
    b = bytes_array[2:]
    return binascii.hexlify(b).decode("utf-8")


def ipfs_to_bytes32(ipfs_hash: str) -> str:
    ipfs_hash_bytes32 = _ipfs_to_bytes32(ipfs_hash)
    return config.w3.toBytes(hexstr=ipfs_hash_bytes32)


def byte_to_mb(size_in_bytes: int) -> int:
    """Instead of a size divisor of 1024 * 1024 you could use the
    bitwise shifting operator (<<), i.e. 1<<20 to get megabytes."""
    MBFACTOR = float(1 << 20)
    return int(size_in_bytes) / MBFACTOR


def generate_md5sum(path: str) -> str:
    if os.path.isdir(path):
        script = f"{env.EBLOCPATH}/bash_scripts/generate_md5sum_for_folder.sh"
        return run(["bash", script, path])

    if os.path.isfile(path):
        tar_hash = check_output(["md5sum", path]).decode("utf-8").strip()
        return tar_hash.split(" ", 1)[0]
    else:
        logging.error(f"{path} does not exist")
        raise


def create_dir(path: str) -> None:
    if not os.path.isdir(path):
        os.makedirs(path)  # mkdir


def getcwd():
    try:
        cwd = os.path.dirnamegetcwd(os.path.abspath(__file__))
    except Exception:
        cwd = os.getcwd()
    return cwd


def eth_address_to_md5(address):
    """Convert Ethereum User Address into 32-bits."""
    return hashlib.md5(address.encode("utf-8")).hexdigest()


def write_to_file(fname, message):
    with open(fname, "w") as f:
        f.write(str(message))


def read_file(fname):
    try:
        file = open(fname, "r")
        return file.read().rstrip()
    except IOError:
        _colorize_traceback()
        raise
    else:
        # else clause instead of finally for things that
        # only happen if there was no exception
        file.close()


def read_json(path, is_dict=True):
    if os.path.isfile(path) and os.path.getsize(path) > 0:
        with open(path) as json_file:
            data = json.load(json_file)
            if is_dict:
                if isinstance(data, dict):
                    return data
                else:
                    return dict()
            else:
                if data:
                    return data
                else:
                    return None
    else:
        raise


def getsize(filename):
    """Return the size of a file, reported by os.stat()."""
    return os.stat(filename).st_size


def path_leaf(path):
    """Return the base name of a path: /<path>/base_name.txt"""
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)


def is_dir_empty(path) -> bool:
    # cmd = ["find", path, "-mindepth", "1", "-print", "-quit"]
    # output = check_output(cmd).decode("utf-8").strip()
    # return not output
    return next(os.scandir(path), None) is None


def remove_empty_files_and_folders(dir_path) -> None:
    """Removes empty files and folders if exists."""
    for root, dirnames, files in os.walk(dir_path, topdown=False):
        for f in files:
            full_name = os.path.join(root, f)
            if os.path.getsize(full_name) == 0:
                try:
                    os.remove(full_name)
                except:
                    pass

        for dirname in dirnames:
            full_path = os.path.realpath(os.path.join(root, dirname))
            if is_dir_empty(full_path):
                try:
                    os.rmdir(full_path)
                except:
                    pass


def printc(text, c="white", is_new_line=True, is_bold=True):
    if is_new_line:
        if is_bold:
            print(colored(f"{COLOR.BOLD}{text}{COLOR.END}", c))
        else:
            print(colored(text, c))
    else:
        if is_bold:
            print(colored(f"{COLOR.BOLD}{text}{COLOR.END}", c), end="")
        else:
            print(colored(text, c), end="")


# TODO: send arguments without order //  is_bold
def log(text, c="white", filename=None, is_new_line=True, is_bold=True):
    text = str(text)
    if threading.current_thread().name != "MainThread" and env.IS_THREADING_ENABLED:
        filename = log_files[threading.current_thread().name]
    elif not filename:
        if env.log_filename:
            filename = env.log_filename
        else:
            filename = env.DRIVER_LOG

    f = open(filename, "a")
    if c:
        if threading.current_thread().name == "MainThread":
            if is_bold:
                printc(colored(f"{COLOR.BOLD}{text}{COLOR.END}", c), c, is_new_line, is_bold)
            else:
                printc(colored(text, c), c, is_new_line, is_bold)
        if is_new_line:
            if is_bold:
                f.write(colored(f"{COLOR.BOLD}{text}\n{COLOR.END}", c))
            else:
                f.write(colored(text, c))
        else:
            if is_bold:
                f.write(colored(f"{COLOR.BOLD}{text}{COLOR.END}", c))
            else:
                f.write(colored(text, c))
    else:
        print(text)
        if is_new_line:
            f.write(f"{text}\n")
        else:
            f.write(text)
    f.close()


def print_trace(cmd, back=1, exc=""):
    _cmd = " ".join(cmd)
    log(f"==> failed_cmd:\n{_cmd}", c="yellow")
    if exc:
        log(f"\n[{WHERE(back)}] Error:\n{exc}", "red")


def WHERE(back=0):
    try:
        frame = sys._getframe(back + 1)
    except:
        frame = sys._getframe(1)
    return "%s:%s %s()" % (os.path.basename(frame.f_code.co_filename), frame.f_lineno, frame.f_code.co_name,)


def silent_remove(path) -> bool:
    """Removes file or folders based on the file type.

    Helpful Links:
    - https://stackoverflow.com/a/10840586/2402577
    """

    try:
        if os.path.isfile(path):
            with suppress(FileNotFoundError):
                os.remove(path)
        elif os.path.isdir(path):
            # deletes a directory and all its contents
            shutil.rmtree(path)
        else:
            return False

        log(f"==> [{WHERE(1)}]\n{path} is removed", "yellow")
        return True
    except Exception as e:
        if e.errno != errno.ENOENT:  # errno.ENOENT = no such file or directory
            _colorize_traceback()
            raise e


def is_ipfs_on() -> bool:
    """Checks whether ipfs runs on the background."""
    return is_process_on("[i]pfs\ daemon", "IPFS", process_count=0)


def is_process_on(process_name, name, process_count=0, port=None) -> bool:
    """Checks wheather the process runs on the background.
    Doc: https://stackoverflow.com/a/6482230/2402577"""
    p1 = Popen(["ps", "aux"], stdout=PIPE)
    p2 = Popen(["grep", "-v", "flycheck_"], stdin=p1.stdout, stdout=PIPE)
    p1.stdout.close()
    p3 = Popen(["grep", "-v", "grep"], stdin=p2.stdout, stdout=PIPE)
    p2.stdout.close()
    p4 = Popen(["grep", "-E", process_name], stdin=p3.stdout, stdout=PIPE)
    p3.stdout.close()
    output = p4.communicate()[0].decode("utf-8").strip().splitlines()
    pids = []
    for line in output:
        fields = line.strip().split()
        # Array indices start at 0 unlike awk, 1 indice points the port number
        pids.append(fields[1])

    if len(pids) > process_count:
        if port:
            # How to find processes based on port and kill them all?
            # https://stackoverflow.com/a/5043907/2402577
            p1 = Popen(["lsof", "-i", f"tcp:{port}"], stdout=PIPE)
            p2 = Popen(["grep", "LISTEN"], stdin=p1.stdout, stdout=PIPE)
            out = p2.communicate()[0].decode("utf-8").strip()
            running_pid = out.strip().split()[1]
            if running_pid in pids:
                log(f"{name} is already running on the background pid={running_pid}", "yellow")
                return True
        else:
            log(f"{name} is already running on the background", "yellow")
            return True
    return False


def is_geth_account_locked(address) -> bool:
    if isinstance(address, int):
        # if given input is an account_id
        return config.w3.geth.personal.list_wallets()[address]["status"] == "Locked"
    else:
        address = config.w3.toChecksumAddress(address)
        for account_idx in range(0, len(config.w3.geth.personal.list_wallets())):
            _address = config.w3.geth.personal.list_wallets()[account_idx]["accounts"][0]["address"]
            if _address == address:
                return config.w3.geth.personal.list_wallets()[account_idx]["status"] == "Locked"
    return False


def is_driver_on(process_count=0) -> bool:
    """Check whether driver runs on the background."""
    if is_process_on("python.*[D]river", "Driver", process_count):
        printc("Track output using:")
        printc(f"tail -f {env.DRIVER_LOG}", "blue")
        raise config.QuietExit
    else:
        return False


def is_ganache_on(port) -> bool:
    """Checks whether Ganache CLI runs on the background."""
    return is_process_on("node.*[g]anache-cli", "Ganache CLI", process_count=0, port=port)


def is_geth_on():
    """Checks whether geth runs on the background."""
    process_name = f"geth|{env.RPC_PORT}"
    print(process_name)
    if not is_process_on(process_name, "Geth", process_count=0):
        log("E: geth is not running on the background. Please run:\nsudo ~/eBlocPOA/server.sh", "red")
        raise config.QuietExit


def is_ipfs_running():
    """Checks that does IPFS run on the background or not."""
    if is_ipfs_on():
        return True

    log("E: IPFS does not work on the background", "blue")
    log("#> Starting IPFS daemon on the background", "blue")
    while True:
        output = run(["python3", f"{env.EBLOCPATH}/python_scripts/run_ipfs_daemon.py"])
        time.sleep(1)
        with open(env.IPFS_LOG, "r") as content_file:
            log(content_file.read(), "blue")
            log(output, "blue")
        if is_ipfs_on():
            return True
    return is_ipfs_on()


def check_ubuntu_packages(packages=None):
    if not packages:
        packages = ["pigz", "curl", "mailutils", "munge"]

    for package in packages:
        if not is_dpkg_installed(package):
            return False
    return True


def is_dpkg_installed(package_name) -> bool:
    try:
        run(["dpkg", "-s", package_name])
        return True
    except:
        return False


def terminate(msg="", is_traceback=True):
    """Terminates Driver and all the dependent python programs to it."""
    if msg:
        log(text=f"[{WHERE(1)}] Termianted \n{msg}", c="red", is_bold=False)

    if is_traceback:
        _colorize_traceback()

    # Following line is added, in case ./killall.sh does not work due to sudo
    # It sends the kill signal to all the process groups
    if config.driver_cancel_process:
        # obtained from global variable
        os.killpg(os.getpgid(config.driver_cancel_process.pid), signal.SIGTERM)

    if config.whisper_state_receiver_process:
        # obtained from global variable, # raise SystemExit("Program Exited")
        os.killpg(os.getpgid(config.whisper_state_receiver_process.pid), signal.SIGTERM)

    try:
        # kill all the dependent processes and exit
        run(["bash", f"{env.EBLOCPATH}/bash_scripts/killall.sh"])
    except:
        sys.exit(1)


def question_yes_no(message, is_terminate=False):
    print(message, end="", flush=True)
    getch = _Getch()
    while True:
        choice = getch().lower()
        if choice in yes:
            break
        elif choice in no or choice == "\x04":
            if is_terminate:
                print("\n")
                terminate()
            else:
                sys.exit()
        else:
            print("\nPlease respond with 'yes' or 'no': ", end="", flush=True)


def json_pretty(json_data):
    """Prints json in readeable clean format."""
    print(json.dumps(json_data, indent=4, sort_keys=True))


def compress_folder(folder_to_share):
    """Compress folder using tar
    - Note that to get fully reproducible tarballs, you should also impose the sort order used by tar

    Helpful Links:
    - https://unix.stackexchange.com/a/438330/198423  == (tar produces different files each time)
    - https://unix.stackexchange.com/questions/580685/why-does-the-pigz-produce-a-different-md5sum
    """
    base_name = os.path.basename(folder_to_share)
    dir_path = os.path.dirname(folder_to_share)

    with cd(dir_path):
        """cmd:
        find . -print0 | LC_ALL=C sort -z | \
        PIGZ=-n tar -Ipigz --mode=a+rwX --owner=0 --group=0 --numeric-owner --absolute-names \
                    --no-recursion --null -T - -zcvf $tar_hash.tar.gz
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
            env={"PIGZ": "-n"},  # alternative: GZIP
        )
        p2.stdout.close()
        p3.communicate()

        tar_hash = generate_md5sum(f"{base_name}.tar.gz")
        tar_file = f"{tar_hash}.tar.gz"
        shutil.move(f"{base_name}.tar.gz", tar_file)
        log(f"Created tar file={dir_path}/{tar_file}")
    return tar_hash, f"{dir_path}/{tar_file}"


class Link:
    def __init__(self, path_from, path_to) -> None:
        self.path_from = path_from
        self.path_to = path_to
        self.data_map = {}

    def link_folders(self, paths=None):
        """Creates linked folders under data_link/ folder"""
        from os import listdir
        from os.path import isdir, join
        from lib import run_command, printc

        if not paths:
            # instead of full path only returns folder names
            paths = [f for f in listdir(self.path_from) if isdir(join(self.path_from, f))]
            is_only_folder_names = True
        else:
            is_only_folder_names = False

        for target in paths:
            if is_only_folder_names:
                folder_name = target
                target = f"{self.path_from}/{target}"
            else:
                folder_name = path_leaf(target)

            folder_hash = generate_md5sum(target)
            self.data_map[folder_name] = folder_hash
            destination = f"{self.path_to}/{folder_hash}"
            run_command(["ln", "-sfn", target, destination])
            printc(f"{target} [is linked to]\n{destination}", "blue")
            folder_new_hash = generate_md5sum(destination)
            assert folder_hash == folder_new_hash


class cd:
    """Context manager for changing the current working directory.
    doc: https://stackoverflow.com/a/13197763/2402577
    """
    def __init__(self, new_path):
        self.new_path = os.path.expanduser(new_path)

    def __enter__(self):
        self.saved_path = os.getcwd()
        os.chdir(self.new_path)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.saved_path)
