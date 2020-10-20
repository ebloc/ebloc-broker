#!/usr/bin/env python3

from config import env
from utils import cd, extract_gzip, run, silent_remove


def decrypt_using_gpg(base, filename, output):
    """General solution to decrypt a file"""
    with cd(base):
        cmd = [
            "gpg",
            "--batch",
            "--yes",
            f"--output={output}",
            "--pinentry-mode",
            "loopback",
            f"--passphrase-file={env.LOG_PATH}/.gpg_pass.txt",
            "--decrypt",
            filename,
        ]
        run(cmd)
        silent_remove(filename)
        extract_gzip(output)
