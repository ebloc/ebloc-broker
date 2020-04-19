#!/usr/bin/env python3

import sys

from config import bp, env, logging  # noqa: F401
from imports import connect
from lib import StorageID
from utils import _colorize_traceback, ipfs_to_bytes


def process_payment(
    job_key,
    index,
    job_id,
    execution_time_min,
    result_ipfs_hash,
    cloud_storage_ids,
    end_time,
    dataTransferIn,
    dataTransferOut,
    core,
    executionDuration,
):
    logging.info(
        f"~/eBlocBroker/contractCalls/process_payment.py {job_key} {index} {job_id} {execution_time_min} {result_ipfs_hash} {cloud_storage_ids} {end_time} {dataTransferIn} {dataTransferOut} '{core}' '{executionDuration}'"
    )

    eBlocBroker, w3 = connect()

    for cloud_storage_id in cloud_storage_ids:
        if len(result_ipfs_hash) != 46 and (
            StorageID.IPFS.value == cloud_storage_id or StorageID.IPFS_MINILOCK.value == cloud_storage_id
        ):
            logging.error("E: Result ipfs's length does not match with its original length. Please check your job_key")
            raise

    try:
        if result_ipfs_hash == b"" or not result_ipfs_hash:
            _result_ipfs_hash = ""
        else:
            _result_ipfs_hash = ipfs_to_bytes(result_ipfs_hash)

        final_job = True  # true only for the final job
        args = [
            int(index),
            int(job_id),
            int(end_time),
            int(dataTransferIn),
            int(dataTransferOut),
            core,
            executionDuration,
            final_job,
        ]
        tx = eBlocBroker.functions.processPayment(job_key, args, int(execution_time_min), _result_ipfs_hash).transact(
            {"from": env.PROVIDER_ID, "gas": 4500000}
        )
    except Exception:
        logging.error(_colorize_traceback())
        raise

    return tx.hex()


if __name__ == "__main__":
    if len(sys.argv) == 12:
        args = sys.argv[1:]
        my_args = []
        for arg in args:
            if arg.startswith("[") and arg.endswith("]"):
                arg = arg.replace("[", "").replace("]", "")
                my_args.append(arg.split(","))
            else:
                my_args.append(arg)

        print(args)
        job_key = str(my_args[0])
        index = int(my_args[1])
        job_id = int(my_args[2])
        execution_time_min = int(my_args[3])
        result_ipfs_hash = str(my_args[4])
        cloud_storage_id = int(my_args[5])
        end_time = int(my_args[6])
        dataTransferIn = float(my_args[7])
        dataTransferOut = float(my_args[8])
        core = my_args[9]
        executionDuration = my_args[10]
    else:  # dummy call
        job_key = "cdd786fca7ab7aa0c55bc039c6c68137"
        index = 0
        job_id = 0
        execution_time_min = 1
        result_ipfs_hash = b""
        cloud_storage_id = 1
        end_time = 1584375940
        dataTransferIn = 0.029152870178222656
        dataTransferOut = 0.0
        core = [1]
        executionDuration = [5]

    try:
        tx_hash = process_payment(
            job_key,
            index,
            job_id,
            execution_time_min,
            result_ipfs_hash,
            cloud_storage_id,
            end_time,
            dataTransferIn,
            dataTransferOut,
            core,
            executionDuration,
        )
        print(f"tx_hash={tx_hash}")
    except:
        sys.exit(1)
