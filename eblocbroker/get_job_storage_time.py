#!/usr/bin/env python3

import sys

import eblocbroker.Contract as Contract

if __name__ == "__main__":
    Ebb = Contract.eblocbroker
    if len(sys.argv) == 3:
        providerAddress = str(sys.argv[1])
        sourceCodeHash = str(sys.argv[2])
    else:
        providerAddress = "0x57b60037b82154ec7149142c606ba024fbb0f991"
        sourceCodeHash = "acfd2fd8a1e9ccf031db0a93a861f6eb"

    receivedBlockNum, storageTime = Ebb.getJobStorageTime(providerAddress, sourceCodeHash)
    print(
        f"receivedBlockNum={receivedBlockNum}; storageTime={storageTime};"
        f" endBlockTime={receivedBlockNum + storageTime * 240}"
    )
