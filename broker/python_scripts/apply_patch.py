#!/usr/bin/env python3

import os
import sys
from os.path import expanduser
from pathlib import Path

import broker.libs._git as git  # noqa
from broker import cfg
from broker._utils.tools import print_tb
from broker.utils import extract_gzip, log, popen_communicate

ipfs = cfg.ipfs


def analyze_patch(base_dir, ipfs_hash):
    ipfs.get(ipfs_hash, base_dir)
    for fn in os.listdir(base_dir):
        patch_file = f"{base_dir}/{fn}"
        if patch_file.endswith(".diff.gz"):
            extract_gzip(patch_file)

    log(f"To see the results run:\n[white]cat {base_dir}/* | less")


def appy_patch(base_dir, patch_fn):
    r"""Apply path file.

    cmd: perl -pe 's/\x1b.*?[mGKH]//g' alper.patch > good.patch
    """
    patch_file = f"{base_dir}/{patch_fn}"
    base_name = patch_fn.replace(".gz", "")
    diff_file_name = f"{base_dir}/{base_name}"
    if not os.path.isfile(diff_file_name):
        if not os.path.isfile(patch_file):
            print(f"E: {patch_file} file does not exist")
            sys.exit(1)

        if patch_file.endswith(".diff.gz"):
            extract_gzip(patch_file)
    else:
        log(f"==> [m]{diff_file_name}[/m] exists")

    try:
        git.apply_patch(base_dir, patch_file.replace(".gz", ""), is_gpg=False)
    except Exception as e:
        print_tb(e)
        try:
            good_patch = f"{base_dir}/good.patch"
            sep = "~"
            popen_communicate(
                ["perl", "-pe", "s/\x1b.*?[mGKH]//g", str(Path(patch_file)).replace(f"{sep}", f"\{sep}")],
                stdout_fn=good_patch,
            )
            git.apply_patch(base_dir, good_patch, is_gpg=False)
        except Exception as e1:
            print_tb(e1)


def main(base_dir, patch_fn):
    appy_patch(base_dir, patch_fn)


if __name__ == "__main__":
    base_dir = expanduser("~/test_eblocbroker/test_data/base/source_code")
    base_dir_results = expanduser("~/test_eblocbroker/test_data/base/source_code/results")
    patch_fn = (
        "patch~a4fb77ea35ea6dfeed7aa300879a73b76268c136~QmTDHuL6HPC6WMWSRHwHmboasfWsrjpLJEvh9D9pUuRqiy~11.diff.gz"
    )
    # main(base_dir, patch_fn)
    #

    ipfs_hash = ""
    if len(sys.argv) == 2:
        ipfs_hash = sys.argv[1]
        analyze_patch(base_dir_results, ipfs_hash)
