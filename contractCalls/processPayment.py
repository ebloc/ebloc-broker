#!/usr/bin/env python3

import sys
import lib
import traceback

from lib import PROVIDER_ID
from imports import connect

# tx = eB.processPayment(jobKey, [index, jobID], execution_time_min, result_ipfs_hash, end_time, dataTransfer, sourceCodeHashArray, {"from": accounts[0]})


def processPayment(
    jobKey,
    index,
    jobID,
    execution_time_min,
    result_ipfs_hash,
    cloudStorageID,
    end_time,
    dataTransferIn,
    dataTransferOut,
    core,
    executionDuration,
    eBlocBroker=None,
    w3=None,
):
    eBlocBroker, w3 = connect(eBlocBroker, w3)
    _from = w3.toChecksumAddress(PROVIDER_ID)

    if len(result_ipfs_hash) != 46 and (
        lib.StorageID.IPFS.value == cloudStorageID or lib.StorageID.IPFS_MINILOCK.value == cloudStorageID
    ):
        return (False, "E: jobKey's length does not match with its original length. Please check your jobKey")

    try:
        result_ipfs_hash = w3.toBytes(
            hexstr=lib.convertIpfsToBytes32(result_ipfs_hash)
        )  # result_ipfs_hash is converted into byte32 format
        endJob = True  # True only for the final job
        args = [
            int(index),
            int(jobID),
            int(end_time),
            int(dataTransferIn),
            int(dataTransferOut),
            core,
            executionDuration,
            endJob,
        ]

        lib.log(
            "~/eBlocBroker/contractCalls/processPayment.py "
            + jobKey
            + " "
            + str(args)
            + str(int(execution_time_min))
            + str(int(execution_time_min))
            + "\n"
        )
        tx = eBlocBroker.functions.processPayment(jobKey, args, int(execution_time_min), result_ipfs_hash).transact(
            {"from": _from, "gas": 4500000}
        )
    except Exception:
        return False, traceback.format_exc()

    return True, tx.hex()


if __name__ == "__main__":
    if len(sys.argv) == 10:
        jobKey = str(sys.argv[1])
        index = int(sys.argv[2])
        jobID = int(sys.argv[3])
        execution_time_min = int(sys.argv[4])
        result_ipfs_hash = str(sys.argv[5])
        cloudStorageID = int(sys.argv[6])
        end_time = int(sys.argv[7])
        dataTransferIn = (int(sys.argv[8]),)
        dataTransferOut = int(sys.argv[9])
    else:  # Dummy call
        jobKey = "QmY6jUjufnyB2nZe38hRZvmyboxtzRcPkP388Yjfhuomoy"
        index = 4
        jobID = 0
        execution_time_min = 1
        result_ipfs_hash = "0x"
        cloudStorageID = 0
        end_time = 1128590
        dataTransferIn = 0
        dataTransferOut = 0

    status, result = processPayment(
        jobKey,
        index,
        jobID,
        execution_time_min,
        result_ipfs_hash,
        cloudStorageID,
        end_time,
        dataTransferIn,
        dataTransferOut,
    )
    if status:
        print("tx_hash=" + result)
    else:
        print(result)
