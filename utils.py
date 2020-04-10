import binascii
import hashlib
import json
import ntpath
import os
import subprocess
import time

import base58

import config
from config import logging
from settings import init_env

Qm = b"\x12 "
empty_bytes32 = b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"


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


def ipfs_toBytes(ipfs_hash: str) -> str:
    ipfs_bytes_32 = ipfs_to_bytes32(ipfs_hash)
    return config.w3.toBytes(hexstr=ipfs_bytes_32)


def byte_to_mb(size_in_bytes: int) -> int:
    """Instead of a size divisor of 1024 * 1024 you could use the
    << bitwise shifting operator, i.e. 1<<20 to get megabytes."""
    MBFACTOR = float(1 << 20)
    return int(size_in_bytes) / MBFACTOR


def generate_md5sum(path: str) -> str:
    env = init_env()
    if os.path.isdir(path):
        return (
            subprocess.check_output(["bash", f"{env.EBLOCPATH}/bash_scripts/generate_md5sum_for_folder.sh", path])
            .decode("utf-8")
            .rstrip()
        )
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


def read_json(path):
    if os.path.isfile(path) and os.path.getsize(path) > 0:
        with open(path) as json_file:
            return json.load(json_file)


def getsize(filename):
    """Return the size of a file, reported by os.stat()."""
    return os.stat(filename).st_size


class Link:
    def __init__(self, path_from, path_to) -> None:
        self.path_from = path_from
        self.path_to = path_to
        self.data_map = {}

    def link_folders(self):
        """Creates linked folders under data_link folder"""
        from os import listdir
        from os.path import isdir, join
        from lib import run_command

        only_folders = [f for f in listdir(self.path_from) if isdir(join(self.path_from, f))]
        for folder in only_folders:
            target = f"{self.path_from}/{folder}"
            folder_hash = generate_md5sum(target)
            self.data_map[folder] = folder_hash
            destination = f"{self.path_to}/{folder_hash}"
            run_command(["ln", "-sfn", target, destination])
            logging.info(f"{target} is linked to {destination}")
            folder_new_hash = generate_md5sum(destination)
            assert folder_hash == folder_new_hash


def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)
