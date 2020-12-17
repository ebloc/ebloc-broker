#!/usr/bin/env python3

import os
import sys

from broker import cfg
from broker._utils.tools import print_tb


def add_to_ipfs(results_folder):
    """Add result folder into ipfs repo."""
    try:
        result_ipfs_hash = cfg.ipfs.add(results_folder)
        print(result_ipfs_hash)
    except Exception as e:
        print_tb(e)
        sys.exit()

    if os.path.isdir(results_folder):
        basename = os.path.basename(os.path.normpath(results_folder))
        filepath = os.path.dirname(results_folder)

    print(filepath)
    print(basename)
    # shutil.move(results_folder, filepath + '/' + result_ipfs_hash)


results_folder = "/home/alper/DAG"
add_to_ipfs(results_folder)
