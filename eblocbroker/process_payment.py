#!/usr/bin/env python3

import sys
from typing import Any, Union

from config import env, logging
from lib import StorageID, state_code
from utils import _colorize_traceback, ipfs_to_bytes32


def process_payment(
    self,
    job_key,
    index,
    job_id,
    elapsed_time,
    result_ipfs_hash,
    cloud_storage_ids,
    end_time,
    data_transfer_in,
    data_transfer_out,
    core,
    run_time,
):
    logging.info(
        f"\n~/eBlocBroker/eblocbroker/process_payment.py {job_key} {index} {job_id} {elapsed_time}"
        f" {result_ipfs_hash} '{cloud_storage_ids}' {end_time} {data_transfer_in} {data_transfer_out} '{core}'"
        f" '{run_time}'"
    )

    for cloud_storage_id in cloud_storage_ids:
        if len(result_ipfs_hash) != 46 and cloud_storage_id in (StorageID.IPFS, StorageID.IPFS_GPG):
            logging.error("E: Result ipfs's length does not match with its original length. Please check your job_key")
            raise

    self.get_job_info(env.PROVIDER_ID, job_key, index, job_id)
    if self.job_info["stateCode"] == state_code["COMPLETED"]:
        logging.error("Job is completed and already get paid")
        sys.exit(1)

    """
    if self.job_info["stateCode"] == str(state_code["COMPLETED"]):
        logging.error("Job is completed and already get paid")
        sys.exit(1)
    """
    try:
        if result_ipfs_hash == b"" or not result_ipfs_hash:
            _result_ipfs_hash = ""
        else:
            _result_ipfs_hash = ipfs_to_bytes32(result_ipfs_hash)

        final_job = True  # true only for the final job
        args = [
            int(index),
            int(job_id),
            int(end_time),
            int(data_transfer_in),
            int(data_transfer_out),
            core,
            run_time,
            final_job,
        ]
        tx = self.eBlocBroker.functions.processPayment(job_key, args, int(elapsed_time), _result_ipfs_hash).transact(
            {"from": env.PROVIDER_ID, "gas": 4500000}
        )
    except Exception:
        _colorize_traceback()
        raise

    return tx.hex()


if __name__ == "__main__":
    from eblocbroker.Contract import Contract

    contract = Contract()

    if len(sys.argv) == 12:
        args = sys.argv[1:]
        my_args = []  # type: Union[Any]
        for arg in args:
            if arg.startswith("[") and arg.endswith("]"):
                arg = arg.replace("[", "").replace("]", "")
                my_args.append(arg.split(","))
            else:
                my_args.append(arg)

        job_key = str(my_args[0])
        index = int(my_args[1])
        job_id = int(my_args[2])
        elapsed_time = int(my_args[3])
        result_ipfs_hash = str(my_args[4])
        cloud_storage_id = my_args[5]
        end_time = int(my_args[6])
        data_transfer_in = float(my_args[7])
        data_transfer_out = float(my_args[8])
        core = my_args[9]
        run_time = my_args[10]

        # convert all strings in a list to int of the following arguments
        cloud_storage_id = list(map(int, cloud_storage_id))
        core = list(map(int, core))
        run_time = list(map(int, run_time))

    else:  # dummy call
        job_key = "cdd786fca7ab7aa0c55bc039c6c68137"
        index = 0
        job_id = 0
        elapsed_time = 1
        result_ipfs_hash = ""
        cloud_storage_id = 1
        end_time = 1584375940
        data_transfer_in = 0.029152870178222656
        data_transfer_out = 0.0
        core = [1]
        run_time = [5]

    try:
        tx_hash = contract.process_payment(
            job_key,
            index,
            job_id,
            elapsed_time,
            result_ipfs_hash,
            cloud_storage_id,
            end_time,
            data_transfer_in,
            data_transfer_out,
            core,
            run_time,
        )
        print(f"tx_hash={tx_hash}")
    except:
        sys.exit(1)
