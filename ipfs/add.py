#!/usr/bin/env python3

from config import env
from libs import ipfs

path = "/home/netlab/eBlocBroker/base/sourceCode"
base_folder = f"{env.EBLOCPATH}/base"

ipfs_hashes = {}
folders_to_share = []
folders_to_share.append(f"{base_folder}/sourceCode")
folders_to_share.append(f"{base_folder}/data/data1")

for path in folders_to_share:
    success, ipfs_hash = ipfs.add(path)
    # success, ipfs_hash = ipfs.add(path, True)
    ipfs_hashes[path] = ipfs_hash

for k, v in ipfs_hashes.items():
    print(f"{k} => {v}")
