import binascii
import hashlib
import json
import ntpath
import os
import subprocess
import time
import traceback

import base58
from pygments import formatters, highlight, lexers

import config
from config import logging

Qm = b"\x12 "
empty_bytes32 = b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"

yes = set(["yes", "y", "ye"])
no = set(["no", "n"])


def _colorize_traceback():
    tb_text = "".join(traceback.format_exc())
    lexer = lexers.get_lexer_by_name("pytb", stripall=True)
    formatter = formatters.get_formatter_by_name("terminal")
    tb_colored = highlight(tb_text, lexer, formatter)
    return tb_colored


def get_time():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def bytes32_to_string(bytes_array):
    return base58.b58encode(bytes_array).decode("utf-8")


def bytes32_to_ipfs(bytes_array):
    """Convert bytes_array into IPFS hash format."""
    merge = Qm + bytes_array
    return base58.b58encode(merge).decode("utf-8")


def string_to_bytes32(hash_str: str):
    """Convert string into  bytes array."""
    bytes_array = base58.b58decode(hash_str)
    return binascii.hexlify(bytes_array).decode("utf-8")


def ipfs_to_bytes32(hash_str: str):
    """Ipfs hash is converted into byte32 format."""
    bytes_array = base58.b58decode(hash_str)
    b = bytes_array[2:]
    return binascii.hexlify(b).decode("utf-8")


def ipfs_to_bytes(ipfs_hash: str) -> str:
    ipfs_bytes_32 = ipfs_to_bytes32(ipfs_hash)
    return config.w3.toBytes(hexstr=ipfs_bytes_32)


def byte_to_mb(size_in_bytes: int) -> int:
    """Instead of a size divisor of 1024 * 1024 you could use the
    << bitwise shifting operator, i.e. 1<<20 to get megabytes."""
    MBFACTOR = float(1 << 20)
    return int(size_in_bytes) / MBFACTOR


def generate_md5sum(path: str) -> str:
    from settings import init_env

    env = init_env()
    if os.path.isdir(path):
        script = f"{env.EBLOCPATH}/bash_scripts/generate_md5sum_for_folder.sh"
        return subprocess.check_output(["bash", script, path]).decode("utf-8").rstrip()
    else:
        tar_hash = subprocess.check_output(["md5sum", path]).decode("utf-8").strip()
        return tar_hash.split(" ", 1)[0]


def create_dir(path: str) -> None:
    if not os.path.isdir(path):
        os.makedirs(path)


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
        raise
    else:
        # else clause instead of finally for things that
        # only happen if there was no exception
        file.close()


def read_json(path):
    if os.path.isfile(path) and os.path.getsize(path) > 0:
        with open(path) as json_file:
            return json.load(json_file)


def getsize(filename):
    """Return the size of a file, reported by os.stat()."""
    return os.stat(filename).st_size


def path_leaf(path):
    """Return the base name of a path: /<path>/base_name.txt"""
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)


def is_dir_empty(absolute_path):
    # Doc: https://stackoverflow.com/a/46555020/2402577
    try:
        os.rmdir(absolute_path)
        is_empty = True
    except OSError:
        is_empty = False

    return is_empty


class Link:
    def __init__(self, path_from, path_to) -> None:
        self.path_from = path_from
        self.path_to = path_to
        self.data_map = {}

    def link_folders(self, paths=None):
        """Creates linked folders under data_link folder"""
        from os import listdir
        from os.path import isdir, join
        from lib import run_command

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
            logging.info(f"{target} is linked to {destination}")
            folder_new_hash = generate_md5sum(destination)
            assert folder_hash == folder_new_hash
