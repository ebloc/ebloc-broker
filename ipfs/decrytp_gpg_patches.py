#!/usr/bin/env python3

import os
import sys

import ipfshttpclient

from libs.gpg import decrypt_using_gpg
from libs.ipfs import get
from utils import create_dir

try:
    client = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001/http')
except:
    print("Run ipfs daemon")
    sys.exit(1)


if __name__ == "__main__":
    ipfs_hash = "Qmb5agpLXbSWivcxankox4oNe8vFudqyBDsrHVQTkcBsoz"

    res = client.ls(ipfs_hash)
    hashes = []
    names = []
    for _file in res['Objects'][0]["Links"]:
        hashes.append(_file["Hash"])
        names.append(_file["Name"])
        print("hash: " + _file["Hash"])
        print("name: " + _file["Name"])
        print("")

    base_target = "/tmp/ipfs"
    create_dir(base_target)

    base_target = os.path.join(base_target, ipfs_hash)
    create_dir(base_target)

    for idx, _hash in enumerate(hashes):
        gpg_file = os.path.join(base_target, names[idx])
        get(_hash, gpg_file, False)
        output_file = f"{_hash}.diff.gz"
        decrypt_using_gpg(base_target, names[idx], output_file)

    print("List:")
    print(os.listdir(base_target))
