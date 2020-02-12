#!/usr/bin/env python3


def ipfs_bytes_to_string(ipfsID):
    val = web3.fromAscii(ipfsID)
    os.environ["val"] = "1220" + val[2:]
    return os.popen("node bs58.js decode $val").read().replace("\n", "")
