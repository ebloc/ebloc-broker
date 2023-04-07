#!/usr/bin/env python3

import os
from os.path import expanduser

from broker import cfg


def add_to_ipfs(results_folder):
    """Add result folder into ipfs repository."""
    try:
        result_ipfs_hash = cfg.ipfs.add(results_folder)
        print(result_ipfs_hash)
    except Exception as e:
        raise e

    if os.path.isdir(results_folder):
        basename = os.path.basename(os.path.normpath(results_folder))
        filepath = os.path.dirname(results_folder)

    print(filepath)
    print(basename)
    # shutil.move(results_folder, filepath + '/' + result_ipfs_hash)


def main():
    results_folder = expanduser("~/DAG")
    add_to_ipfs(results_folder)


if __name__ == "__main__":
    main()
