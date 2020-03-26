#!/usr/bin/env python3

import sys

from imports import connect


def getJobStorageTime(providerAddress, sourceCodeHash):
    eBlocBroker, w3 = connect()

    providerAddress = w3.toChecksumAddress(providerAddress)
    ret = eBlocBroker.call().getJobStorageTime(providerAddress, sourceCodeHash)
    return ret[0], ret[1]


if __name__ == "__main__":
    if len(sys.argv) == 3:
        providerAddress = str(sys.argv[1])
        sourceCodeHash = str(sys.argv[2])
    else:
        providerAddress = "0x57b60037b82154ec7149142c606ba024fbb0f991"
        sourceCodeHash = "acfd2fd8a1e9ccf031db0a93a861f6eb"

    receivedBlockNum, storageTime = getJobStorageTime(providerAddress, sourceCodeHash)
    print(f"receivedBlockNum={receivedBlockNum}; storageTime={storageTime}; endBlockTime={receivedBlockNum + storageTime * 240}")
