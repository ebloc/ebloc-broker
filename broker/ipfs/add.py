#!/usr/bin/env python3

import sys

from config import env
from libs import ipfs
from utils import _colorize_traceback

base_dir = f"{env.EBLOCPATH}/base"
source_code_path = f"{base_dir}/source_code"

ipfs_hashes = {}
folders_to_share = []
folders_to_share.append(source_code_path)
folders_to_share.append(f"{base_dir}/data/data1")

for path in folders_to_share:
    try:
        ipfs_hash = ipfs.add(path)  # ipfs.add(path, True)
    except:
        _colorize_traceback()
        sys.exit(1)

    ipfs_hashes[path] = ipfs_hash

for k, v in ipfs_hashes.items():
    print(f"{k} => {v}")
