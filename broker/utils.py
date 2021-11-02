#!/usr/bin/env python3

import binascii
import errno
import hashlib
import json
import ntpath
import os
import re
import shlex
import shutil
import signal
import socket
import sys
import time
import traceback
from contextlib import suppress
from enum import IntEnum
from subprocess import PIPE, CalledProcessError, Popen, check_output
from typing import Dict
import base58
from broker import cfg
from broker import config
from broker._utils import _log
from broker._utils._getch import _Getch
from broker._utils.tools import WHERE, QuietExit, is_process_on, log, print_tb, run
from broker.config import env, logging

ETH_ADDRESS = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
Qm = b"\x12 "
empty_bytes32 = b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
zero_bytes32 = "0x00"
yes = set(["yes", "y", "ye", "ys", "yy", "yey"])
no = set(["no", "n", "nn"])
EXIT_FAILURE = 1


class BashCommandsException(Exception):
    def __init__(self, returncode, output, error_msg):
        self.returncode = returncode
        self.output = output
        self.error_msg = error_msg
        Exception.__init__("Error in the executed command")


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


STORAGE_IDs = {
    "ipfs": StorageID.IPFS,
    "eudat": StorageID.EUDAT,
    "ipfs_gpg": StorageID.IPFS_GPG,
    "gdrive": StorageID.GDRIVE,
}

CACHE_TYPES = {
    "public": CacheType.PUBLIC,
    "private": CacheType.PRIVATE,
}


class cd:
    """Context manager for changing the current working directory.

    # enter the directory like this:
    with cd("~/Library"):
        # we are in ~/Library
        subprocess.call("ls")

    # outside the context manager we are back wherever we started.

    __ https://stackoverflow.com/a/13197763/2402577
    """

    def __init__(self, new_path):
        self.saved_path = None
        self.new_path = os.path.expanduser(new_path)

    def __enter__(self):
        self.saved_path = os.getcwd()
        os.chdir(self.new_path)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.saved_path)


def raise_error(error):
    traceback.print_stack()
    raise RuntimeError(error)


def extract_gzip(filename):
    try:
        args = shlex.split(f"gunzip --force {filename}")
        run(args)
    except:
        args = shlex.split(f"zcat {filename}")
        base_dir = os.path.dirname(filename)
        base_name = os.path.basename(filename).replace(".gz", "")
        popen_communicate(args, f"{base_dir}/{base_name}")


def untar(tar_file, extract_to):
    """Untar given tar file.

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
                log(f"==> {tar_file} is already extracted into\n{extract_to}")
                return
    # tar --warning=no-timestamp
    cmd = ["tar", "--warning=no-timestamp", "-xvpf", tar_file, "-C", extract_to, "--no-overwrite-dir", "--strip", "1"]
    run(cmd)


def is_internet_on(host="8.8.8.8", port=53, timeout=3) -> bool:
    """Check wheather internet is online.

    Host: 8.8.8.8 (google-public-dns-a.google.com)
    OpenPort: 53/tcp
    Service: domain (DNS/TCP)

    https://stackoverflow.com/a/33117579/2402577
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error as ex:
        print(ex)
        return False


def sleep_timer(sleep_duration):
    log(f"Sleeping for {sleep_duration} seconds, called from {WHERE(1)}", "blue")
    for remaining in range(sleep_duration, 0, -1):
        sys.stdout.write("\r")
        sys.stdout.write("{:1d} seconds remaining...".format(remaining))
        sys.stdout.flush()
        time.sleep(1)
    sys.stdout.write("\rSleeping is done                                \n")


def remove_ansi_escape_sequence(string):
    """Remove ansi escape sequence.

    __ https://stackoverflow.com/questions/14693701/how-can-i-remove-the-ansi-escape-sequences-from-a-string-in-python
    """
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", string)


def _try(func):
    """Call given function inside try and except.

    Example called: _try(lambda: f())
    Returns status and output of the function

    :param func: yield function
    :raises:
        Exception: Explanation here.
    """
    try:
        return func()
    except Exception as e:
        print_tb(e)
        raise e


def is_bin_installed(name):
    try:
        run(["which", name])
    except Exception as e:
        log(f"E: [green]{name}[/green] is not instelled")
        raise e


def run_with_output(cmd):
    # https://stackoverflow.com/questions/4417546/constantly-print-subprocess-output-while-process-is-running
    cmd = list(map(str, cmd))  # all items should be string
    ret = ""
    with Popen(cmd, stdout=PIPE, bufsize=1, universal_newlines=True) as p:
        for line in p.stdout:
            ret += line.strip()
            print(line, end="")  # process line here
        return ret

    if p.returncode != 0:
        raise CalledProcessError(p.returncode, p.args)


def popen_communicate(cmd, stdout_file=None, mode="w", _env=None):
    """Act similir to run(cmd).

    But also returns the output message captures on during the run stdout_file
    is not None in case of nohup process writes its results into a file.
    """
    cmd = list(map(str, cmd))  # all items should be str
    if stdout_file is None:
        p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    else:
        with open(stdout_file, mode) as outfile:
            # output written into file, error will be returned
            p = Popen(cmd, stdout=outfile, stderr=PIPE, env=_env, universal_newlines=False)
            output, error = p.communicate()
            p.wait()
            return p, output, error.rstrip()

    output, error = p.communicate()
    if output:
        output = output.strip().decode("utf-8")

    if error:
        error = error.decode("utf-8")

    return p, output, error.rstrip()


def is_transaction_valid(tx_hash) -> bool:
    pattern = re.compile(r"^0x[a-fA-F0-9]{64}")
    return bool(re.fullmatch(pattern, tx_hash))


def is_transaction_passed(tx_hash) -> bool:
    receipt = cfg.w3.eth.getTransactionReceipt(tx_hash)
    with suppress(Exception):
        if receipt["status"] == 1:
            return True

    return False


def insert_character(string, index, char) -> str:
    return string[:index] + char + string[index:]


def get_time():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def bytes_to_string(_bytes):
    return _bytes.decode("utf-8")


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


def ipfs_to_bytes32(ipfs_hash: str) -> bytes:
    ipfs_hash_bytes32 = _ipfs_to_bytes32(ipfs_hash)
    return cfg.w3.toBytes(hexstr=ipfs_hash_bytes32)


def byte_to_mb(size_in_bytes: float) -> int:
    """Instead of a size divisor of 1024 * 1024 you could use the
    bitwise shifting operator (<<), i.e. 1<<20 to get megabytes."""
    MBFACTOR = float(1 << 20)
    return int(int(size_in_bytes) / MBFACTOR)


def generate_md5sum(path: str) -> str:
    if os.path.isdir(path):
        return run([env.BASH_SCRIPTS_PATH / "generate_md5sum_for_folder.sh", path])

    if os.path.isfile(path):
        tar_hash = check_output(["md5sum", path]).decode("utf-8").strip()
        return tar_hash.split(" ", 1)[0]
    else:
        logging.error(f"E: {path} does not exist")
        raise


def getcwd():
    try:
        cwd = os.path.dirnamegetcwd(os.path.abspath(__file__))
    except:
        cwd = os.getcwd()
    return cwd


def eth_address_to_md5(address):
    """Convert Ethereum User Address into 32-bits."""
    return hashlib.md5(address.encode("utf-8")).hexdigest()


def write_to_file(fname, message) -> None:
    with open(fname, "w") as f:
        f.write(str(message))


def read_file(fname):
    try:
        file = open(fname, "r")
        return file.read().rstrip()
    except IOError as e:
        print_tb(e)
        raise e
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
                    return {}
            else:
                if data:
                    return data
                else:
                    return None
    else:
        raise


def is_gzip_file_empty(filename):
    """Check whether the given gzip file is empty or not.

    cmd: gzip -l filename.gz | awk 'NR==2 {print $2}
    """
    p1 = Popen(["gzip", "-l", filename], stdout=PIPE, env={"LC_ALL": "C"})
    p2 = Popen(["awk", "NR==2 {print $2}"], stdin=p1.stdout, stdout=PIPE)
    p1.stdout.close()
    size = p2.communicate()[0].decode("utf-8").strip()
    if bool(int(size)):
        return False

    log(f"==> Created gzip file ({filename}) is empty")
    return True


def getsize(filename):
    """Return the size of a file, reported by os.stat()."""
    return os.stat(filename).st_size


def path_leaf(path):
    """Return the base name of a path: '/<path>/base_name.txt'."""
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)


def is_dir_empty(path) -> bool:
    # cmd = ["find", path, "-mindepth", "1", "-print", "-quit"]
    # output = check_output(cmd).decode("utf-8").strip()
    # return not output
    return next(os.scandir(path), None) is None


def remove_empty_files_and_folders(dir_path) -> None:
    """Remove empty files and folders if exists."""
    for root, dirnames, files in os.walk(dir_path, topdown=False):
        for _file in files:
            full_path = os.path.join(root, _file)
            if os.path.getsize(full_path) == 0:
                with suppress(Exception):
                    os.remove(full_path)

        for dirname in dirnames:
            full_path = os.path.realpath(os.path.join(root, dirname))
            if is_dir_empty(full_path):
                with suppress(Exception):
                    os.rmdir(full_path)


def _remove(path: str, is_warning=True):
    """Remove file or folders based on its the file type.

    __ https://stackoverflow.com/a/10840586/2402577
    """
    try:
        if path == "/":
            raise ValueError("E: Attempting to remove /")

        if os.path.isfile(path):
            with suppress(FileNotFoundError):
                os.remove(path)
        elif os.path.isdir(path):
            # deletes a directory and all its contents
            shutil.rmtree(path)
        else:
            if is_warning:
                log(f"Warning: {WHERE(1)} Given path '{path}' does not exists. Nothing is removed.")
            return

        log(f"==> {WHERE(1)}\n{path} is removed")
    except OSError as e:
        # Suppress the exception if it is a file not found error.
        # Otherwise, re-raise the exception.
        if e.errno != errno.ENOENT:
            print_tb(e)
            raise e


def is_ipfs_on(is_print=True) -> bool:
    """Check whether ipfs runs on the background."""
    return is_process_on("[i]pfs\ daemon", "IPFS", process_count=0, is_print=is_print)


def is_geth_account_locked(address) -> bool:
    if isinstance(address, int):
        # if given input is an account_id
        return cfg.w3.geth.personal.list_wallets()[address]["status"] == "Locked"
    else:
        address = cfg.w3.toChecksumAddress(address)
        for account_idx in range(0, len(cfg.w3.geth.personal.list_wallets())):
            _address = cfg.w3.geth.personal.list_wallets()[account_idx]["accounts"][0]["address"]
            if _address == address:
                return cfg.w3.geth.personal.list_wallets()[account_idx]["status"] == "Locked"
    return False


def is_driver_on(process_count=0, is_print=True):
    """Check whether driver runs on the background."""
    if is_process_on("python.*[D]river", "Driver", process_count, is_print=is_print):
        log(f"## Track output using:\n[blue]tail -f {_log.DRIVER_LOG}")
        raise QuietExit


def is_ganache_on(port) -> bool:
    """Check whether Ganache CLI runs on the background."""
    return is_process_on("node.*[g]anache-cli", "Ganache CLI", process_count=0, port=port)


def is_geth_on():
    """Check whether geth runs on the background."""
    process_name = f"geth@{env.RPC_PORT}"
    if not is_process_on(process_name, "Geth", process_count=0):
        log(f"E: geth is not running on the background, {process_name}. Please run:")
        log("sudo ~/eBlocPOA/server.sh", "bold yellow")
        raise QuietExit


def run_ipfs_daemon():
    """Check that does IPFS run on the background or not."""
    if is_ipfs_on():
        return True

    log("Warning: [green]IPFS[/green] does not work on the background")
    log("#> Starting [green]IPFS daemon[/green] on the background")
    output = run(["python3", env.EBLOCPATH / "broker" / "python_scripts" / "run_ipfs_daemon.py"])
    while True:
        time.sleep(1)
        with open(env.IPFS_LOG, "r") as content_file:
            log(content_file.read(), "bold blue")
            log(output, "bold blue")

        if is_ipfs_on():
            return True
    return False


def check_ubuntu_packages(packages=None):
    if not packages:
        packages = ["pigz", "curl", "mailutils", "munge", "git"]

    for package in packages:
        if not is_dpkg_installed(package):
            return False
    return True


def is_npm_installed(package_name) -> bool:
    output = run(["npm", "list", "-g", "--depth=0"])
    return package_name in output


def is_dpkg_installed(package_name) -> bool:
    try:
        run(["dpkg", "-s", package_name])
        return True
    except:
        return False


def terminate(msg="", is_traceback=True, lock=None):
    """Terminate the Driver python script and all the dependent python programs to it."""
    if msg:
        log(f"{WHERE(1)} Terminated: ", "bold red", end="")
        log(msg, "bold")

    if is_traceback:
        print_tb()

    if lock:
        with suppress(Exception):
            lock.close()

    if config.driver_cancel_process:
        # Following line is added, in case ./killall.sh does not work due to
        # sudo It sends the kill signal to all the process groups, pid is
        # obtained from the global variable
        os.killpg(os.getpgid(config.driver_cancel_process.pid), signal.SIGTERM)

    try:
        # kill all the dependent processes and exit
        run([env.BASH_SCRIPTS_PATH / "killall.sh"])
    except:
        sys.exit(1)


def question_yes_no(message, is_terminate=False):
    log(text=message, end="", flush=True)
    getch = _Getch()
    while True:
        choice = getch().lower()
        if choice in yes:
            log(choice)
            break
        elif choice in no or choice in ["\x04", "\x03"]:
            if is_terminate:
                log("\n")
                terminate()
            else:
                sys.exit(1)
        else:
            log("Please respond with [green]yes[/green] or [green]no[/green]: ")


def json_pretty(json_data):
    """Print json in readeable clean format."""
    print(json.dumps(json_data, indent=4, sort_keys=True))


def is_program_valid(cmd):
    try:
        run(cmd)
    except Exception as e:
        terminate(f"Please install {cmd[0]} or check its path.\n{e}", is_traceback=False)


def compress_folder(folder_path, is_exclude_git=False):
    """Compress folder using tar.

    :param folder_path: should be full path

    Note that to get fully reproducible tarballs, you should also impose the
    sort order used by tar

    __ https://unix.stackexchange.com/a/438330/198423  == (Eac time tar produces different files)
    __ https://unix.stackexchange.com/questions/580685/why-does-the-pigz-produce-a-different-md5sum
    """
    base_name = os.path.basename(folder_path)
    dir_path = os.path.dirname(folder_path)
    tar_base = f"{base_name}.tar.gz"
    with cd(dir_path):
        """cmd:
        find . -print0 | LC_ALL=C sort -z | \
            PIGZ=-n tar -Ipigz --mtime='1970-01-01 00:00:00' --mode=a+rwX --owner=0 \
            --group=0 --numeric-owner --no-recursion \
            --null -T - -cvf /tmp/work/output.tar.gz && md5sum /tmp/work/output.tar.gz
        """
        cmd = [
            "tar",
            "-Ipigz",
            "--exclude=.mypy_cache",  # exclude some hidden folders
            "--exclude=.venv",
            "--mtime=1970-01-01 00:00:00",
            "--mode=a+rwX",
            "--owner=0",
            "--group=0",
            # "--absolute-names",  # --absolute-names is not needed, since absolute paths are not used
            "--numeric-owner",
            "--no-recursion",
            "--null",
            "-T",
            "-",
            "-cvf",
            tar_base,
        ]
        if is_exclude_git:
            # consider ignoring to add .git into the requested folder
            idx = 2
            cmd = cmd[:idx] + ["--exclude=.git"] + cmd[idx:]

        p1 = Popen(["find", base_name, "-print0"], stdout=PIPE)
        p2 = Popen(["sort", "-z"], stdin=p1.stdout, stdout=PIPE, env={"LC_ALL": "C"})
        p1.stdout.close()
        p3 = Popen(
            cmd,
            stdin=p2.stdout,
            stdout=PIPE,
            env={"PIGZ": "-n"},
        )  # __  "GZIP" alternative
        p2.stdout.close()
        p3.communicate()
        tar_hash = generate_md5sum(tar_base)
        tar_file = f"{tar_hash}.tar.gz"
        shutil.move(tar_base, tar_file)
        log(f"==> Created tar file={dir_path}/{tar_file}")
        log(f"==> tar_hash={tar_hash}")
    return tar_hash, f"{dir_path}/{tar_file}"


def dump_dict_to_file(filename, job_keys):
    with open(filename, "w") as f:
        json.dump(job_keys, f)


class Link:
    def __init__(self, path_from, path_to) -> None:
        self.data_map = {}  # type: Dict[str, str]
        self.path_from = path_from  # Path automatically removes / at the end if there is
        self.path_to = path_to

    def link_folders(self, paths=None):
        """Create linked folders under the data_link folder."""
        from os import listdir
        from os.path import isdir, join

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

            try:
                folder_hash = generate_md5sum(target)
            except Exception as e:
                raise e

            self.data_map[folder_name] = folder_hash
            destination = f"{self.path_to}/{folder_hash}"
            run(["ln", "-sfn", target, destination])
            log(f" *   [bold green]{target}[/bold green]", "bold yellow")
            log(f" └─> {destination}", "bold yellow")
            folder_new_hash = generate_md5sum(destination)
            assert folder_hash == folder_new_hash, "Hash does not match original and linked folder"
