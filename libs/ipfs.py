#!/usr/bin/env python3
import os
import subprocess

from config import bp, logging  # noqa: F401
from lib import compress_folder, run_command, silent_remove


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


def mlck_encrypt(provider_minilock_id, mlck_pass, target):
    is_delete = False
    if os.path.isdir(target):
        tar_hash, target = compress_folder(target)
        is_delete = True

    cmd = ["mlck", "encrypt", "-f", target, provider_minilock_id, f"--passphrase={mlck_pass}"]
    success, output = run_command(cmd)
    if is_delete:
        silent_remove(target)

    return success, f"{target}.minilock"
