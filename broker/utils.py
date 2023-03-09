#!/usr/bin/env python3

import binascii
import hashlib
import json
import ntpath
import os
import shlex
import shutil
import signal
import socket
import sys
import time
import traceback
from contextlib import suppress
from enum import IntEnum
from subprocess import PIPE, Popen, check_output

import base58

from broker import cfg, config
from broker._utils import _log
from broker._utils._getch import _Getch
from broker._utils._log import WHERE, br
from broker._utils.tools import _exit, is_process_on, log, pre_cmd_set, print_tb, run
from broker.config import env
from broker.errors import QuietExit

Qm = b"\x12 "
zero_bytes32 = "0x00"
empty_bytes32 = (
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
)


class BaseEnum(IntEnum):
    def __int__(self):
        return int(self.value)

    def __str__(self):
        return str(self.value)

    def __eq__(self, other):
        return int(self.value) == other


class CacheType(BaseEnum):
    PUBLIC = 0
    PRIVATE = 1


class StorageID(BaseEnum):
    IPFS = 0
    IPFS_GPG = 1
    NONE = 2
    B2DROP = 3
    GDRIVE = 4


CACHE_TYPES = {
    "public": CacheType.PUBLIC,
    "private": CacheType.PRIVATE,
}

STORAGE_IDs = {
    "ipfs": StorageID.IPFS,
    "ipfs_gpg": StorageID.IPFS_GPG,
    "b2drop": StorageID.B2DROP,
    "gdrive": StorageID.GDRIVE,
    "none": StorageID.NONE,
}


class cd:
    """Context manager for changing the current working directory.

    - Outside the context manager we are back wherever we started.

    - Enter the directory like this:
    with cd("/home/to/folder"):
        # we are in /home/to/folder
        subprocess.call("ls")

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


def extract_gzip(fn):
    try:
        args = shlex.split(f"gunzip --force {fn}")
        run(args)
    except:
        args = shlex.split(f"zcat {fn}")
        base_dir = os.path.dirname(fn)
        base_name = os.path.basename(fn).replace(".gz", "")
        popen_communicate(args, f"{base_dir}/{base_name}")


def untar(tar_fn, extract_to):
    """Extract the given tar file.

    umask can be ignored by using the -p (--preserve) option
        --no-overwrite-dir: preserve metadata of existing directories

    tar interprets the next argument after -f as the file name of the tar file.
    Put the p before the f:
    """
    fn = os.path.basename(tar_fn)
    accepted_files = [".git", fn]
    if not is_dir_empty(extract_to):
        for name in os.listdir(extract_to):
            # if tar itself already exist inside the same directory along with `.git` file
            if name not in accepted_files:
                log(f"==> {tar_fn} is already extracted into\n    {extract_to}")
                return

    run(["tar", "--warning=no-timestamp", "-xvpf", tar_fn, "-C", extract_to, "--no-overwrite-dir", "--strip", "1"])


def is_internet_on(host="8.8.8.8", port=53, timeout=3) -> bool:
    """Check whether internet is online.

    Host: 8.8.8.8 (google-public-dns-a.google.com)
    OpenPort: 53/tcp
    Service: domain (DNS/TCP)

    __ https://stackoverflow.com/a/33117579/2402577
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error as e:
        log(f"E: {e}")
        raise e


def sleep_timer(sleep_duration):
    log(f"#> sleeping for {sleep_duration} seconds, called from {WHERE(1)}")
    for remaining in range(sleep_duration, 0, -1):
        sys.stdout.write("\r")
        sys.stdout.write("{:1d} seconds remaining...".format(remaining))
        sys.stdout.flush()
        time.sleep(1)

    sys.stdout.write("\rsleeping is done                                \n")


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
        log(f"E: [g]{name}[/g] is not instelled")
        raise e


def popen_communicate(cmd, stdout_fn=None, mode="w", env=None):
    """Act similir to the `run()` function.

    But also returns the output message captures on during the run stdout_fn
    is not None in case of nohup process writes its results into a file.

    * How to catch exception output from Python subprocess.check_output()?:
    __ https://stackoverflow.com/a/24972004/2402577
    """
    cmd = pre_cmd_set(cmd)
    if stdout_fn is None:
        p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    else:
        with open(stdout_fn, mode) as outfile:
            # output written into file, error will be returned
            p = Popen(cmd, stdout=outfile, stderr=PIPE, env=env, universal_newlines=False)
            output, error = p.communicate()
            p.wait()
            return p, output, error.rstrip()

    output, error = p.communicate()
    if output:
        output = output.strip().decode("utf-8")

    if error:
        error = error.decode("utf-8").rstrip()

    return p, output, error


def insert_character(string, index, char) -> str:
    return string[:index] + char + string[index:]


def get_date():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def bytes_to_string(_bytes):
    return _bytes.decode("utf-8")


def bytes32_to_string(bytes_array):
    return base58.b58encode(bytes_array).decode("utf-8")


def string_to_bytes32(hash_str: str):
    """Convert string into  bytes array."""
    bytes_array = base58.b58decode(hash_str)
    return binascii.hexlify(bytes_array).decode("utf-8")


def bytes32_to_ipfs(bytes_array, is_verbose=True):
    """Convert bytes_array into IPFS hash format."""
    if bytes_array in (b"", ""):
        return ""

    if isinstance(bytes_array, bytes):
        return base58.b58encode(Qm + bytes_array).decode("utf-8")
    elif is_verbose:
        log(f"warning: bytes_array={bytes_array} is not a bytes instance")

    return bytes_array


def is_ipfs_hash_valid(ipfs_hash: str) -> bool:
    return bool(len(ipfs_hash) == 46 and ipfs_hash[:2] == "Qm")


def ipfs_to_bytes32(ipfs_hash: str) -> bytes:
    """Convert ipfs hash into bytes32 format."""
    if is_ipfs_hash_valid(ipfs_hash):
        bytes_array = base58.b58decode(ipfs_hash)
        b = bytes_array[2:]
        return cfg.w3.toBytes(hexstr=binascii.hexlify(b).decode("utf-8"))
    else:
        raise Exception("Not valid ipfs hash given")


def byte_to_mb(size_in_bytes: float) -> int:
    """Convert byte into MB.

    Instead of a size divisor of 1024 * 1024 you could use the
    bitwise shifting operator (<<), i.e. 1<<20 to get megabytes.
    """
    MBFACTOR = float(1 << 20)
    return int(int(size_in_bytes) / MBFACTOR)


def generate_md5sum(path: str) -> str:
    if os.path.isdir(path):
        return run([env.BASH_SCRIPTS_PATH / "generate_md5sum_for_folder.sh", path])

    if os.path.isfile(path):
        tar_hash = check_output(["md5sum", path]).decode("utf-8").strip()
        return tar_hash.split(" ", 1)[0]
    else:
        raise Exception(f"{path} does not exist")


def eth_address_to_md5(address):
    """Convert ethereum user address into 32-bits."""
    return hashlib.md5(address.encode("utf-8")).hexdigest()


def write_to_file(fn, message) -> None:
    with open(fn, "w") as f:
        f.write(str(message))


def read_file(fn):
    try:
        file = open(fn, "r")
        return file.read().rstrip()
    except IOError as e:
        print_tb(e)
        raise e
    else:
        # else clause instead of finally for things that
        # only happen if there was no exception
        file.close()


def is_gzip_file_empty(fn):
    """Check whether the given gzip file is empty or not.

    cmd: gzip -l fn.gz | awk 'NR==2 {print $2}
    """
    p1 = Popen(["gzip", "-l", fn], stdout=PIPE, env={"LC_ALL": "C"})
    p2 = Popen(["awk", "NR==2 {print $2}"], stdin=p1.stdout, stdout=PIPE)
    p1.stdout.close()
    size = p2.communicate()[0].decode("utf-8").strip()
    if bool(int(size)):
        return False

    log(f"==> Created gzip file is empty:\n    [m]{fn}[/m]")
    return True


def getsize(fn):
    """Return the size of a file, reported by os.stat()."""
    return os.stat(fn).st_size


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


def is_ipfs_on(is_print=False) -> bool:
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


def is_driver_on(process_count=1, is_print=True):
    """Check whether driver runs on the background."""
    if is_process_on("python.*[e]blocbroker driver", process_count=process_count, is_print=is_print):
        log(f"## Track output using: [blue]tail -f {_log.DRIVER_LOG}")
        raise QuietExit


def is_geth_on():
    """Check whether geth runs on the background."""
    process_name = f"geth@{env.RPC_PORT}"
    if not is_process_on(process_name, "Geth", process_count=0):
        log(f"E: geth is not running on the background, {process_name}. Please run:")
        log("sudo ~/eBlocPOA/server.sh", "bold yellow")
        raise QuietExit


def is_ganache_on(port) -> bool:
    """Check whether ganache-cli runs on the background."""
    return is_process_on("node.*[g]anache-cli", "ganache-cli", process_count=0, port=port)


def start_ipfs_daemon(_is_print=False) -> bool:
    """Check that does IPFS run on the background or not."""
    if is_ipfs_on(_is_print):
        return True

    try:
        output = run(["/usr/local/bin/ipfs", "repo", "stat"])
    except Exception as e:
        raise QuietExit from e

    log("warning: [g]IPFS[/g] does not work on the background")
    log("#> Starting [g]IPFS daemon[/g] on the background")
    output = run(["python3", env.EBLOCPATH / "broker" / "_daemons" / "ipfs.py"])
    while True:
        time.sleep(1)
        with open(env.IPFS_LOG, "r") as content_file:
            log(content_file.read().rstrip(), "bold blue")
            time.sleep(5)  # in case sleep for 5 seconds
            if output:
                log(output.replace("==> Running IPFS daemon", "").rstrip(), "blue")

        if is_ipfs_on(is_print=True):
            return True

    return False


def check_ubuntu_packages(packages=None) -> bool:
    if not packages:
        packages = ["pigz", "curl", "mailutils", "munge", "git"]

    for package in packages:
        if not is_dpkg_installed(package):
            return False

    return True


def is_npm_installed(package) -> bool:
    return package in run(["npm", "list", "-g", "--depth=0"])


def is_dpkg_installed(package) -> bool:
    try:
        run(["dpkg", "-s", package])
        return True
    except:
        return False


def terminate(msg="", is_traceback=False, lock=None) -> None:
    """Terminate the program and exit."""
    if msg:
        log(f"{WHERE(1)} Terminated: ", "bold red", end="")
        if msg[:3] == "E: ":
            log(msg[3:], "bold")
        else:
            log(msg, "bold")

    if is_traceback:
        print_tb()

    if lock:
        with suppress(Exception):
            lock.close()

    _exit()


def terminate_killall(msg="", is_traceback=True, lock=None):
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


def question_yes_no(message, is_exit=False):
    if "[Y/n]:" not in message:
        message = f"{message} [Y/n]: "

    log(text=message, end="")
    getch = _Getch()
    while True:
        choice = getch().lower()
        if choice in set(["yes", "y", "ye", "ys", "yy", "yey"]):
            log(choice)
            return True
        elif choice in set(["no", "n", "nn"]) or choice in ["\x04", "\x03"]:
            if is_exit:
                log()
                _exit()
                # terminate(is_traceback=False)
            else:
                return False
                # sys.exit(1)
        else:
            log()
            log(
                f"#> Please respond with [bg]{br('y')}es[/bg] or [bg]{br('n')}o[/bg]: ",
                end="",
            )


def json_pretty(json_data) -> None:
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

    __ https://unix.stackexchange.com/a/438330/198423  == (Each time tar produces different files)
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
            #: consider ignoring to add .git into the requested folder
            cmd = cmd[:2] + ["--exclude=.git"] + cmd[2:]

        p1 = Popen(["find", base_name, "-print0"], stdout=PIPE)
        p2 = Popen(["sort", "-z"], stdin=p1.stdout, stdout=PIPE, env={"LC_ALL": "C"})
        p1.stdout.close()
        p3 = Popen(
            cmd,
            stdin=p2.stdout,
            stdout=PIPE,
            env={"PIGZ": "-n"},  # env={"GZIP": "-n"},  # alternative
        )
        p2.stdout.close()
        p3.communicate()
        tar_hash = generate_md5sum(tar_base)
        tar_fn = f"{tar_hash}.tar.gz"
        shutil.move(tar_base, tar_fn)
        log(f"==> created_tar_fn={dir_path}/{tar_fn}")
        log(f"==> tar_hash={tar_hash}")

    return tar_hash, f"{dir_path}/{tar_fn}"


def dump_dict_to_file(fn, job_keys):
    with open(fn, "w") as f:
        json.dump(job_keys, f)
