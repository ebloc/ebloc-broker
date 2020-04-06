#!/usr/bin/env python3
import subprocess

from config import bp, logging  # noqa: F401
from lib import run_command


def get_hash(ipfs_hash, path, is_storage_paid):
    output = subprocess.check_output(["ipfs", "get", ipfs_hash, f"--output={path}"]).decode("utf-8").rstrip()
    logging.info(output)

    if is_storage_paid:
        # Pin downloaded ipfs hash if storage is paid
        output = subprocess.check_output(["ipfs", "pin", "add", ipfs_hash]).decode("utf-8").rstrip()
        logging.info(output)


def pin(ipfs_hash) -> bool:
    cmd = ["ipfs", "pin", "add", ipfs_hash]
    success, output = run_command(cmd, None, True)
    print(output)
    return success
