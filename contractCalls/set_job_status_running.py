#!/usr/bin/env python3

import sys
import traceback

from imports import connect

from settings import init_env


def set_job_status_running(_key, index, job_id, startTime):
    eBlocBroker, w3 = connect()
    env = init_env()
    if eBlocBroker is None or w3 is None:
        return

    try:
        tx = eBlocBroker.functions.setJobStatusRunning(_key, int(index), int(job_id), int(startTime)).transact(
            {"from": w3.toChecksumAddress(env.PROVIDER_ID), "gas": 4500000}
        )
    except Exception:
        return False, traceback.format_exc()

    return True, tx.hex()


if __name__ == "__main__":
    if len(sys.argv) == 5:
        key = str(sys.argv[1])
        index = int(sys.argv[2])
        job_id = int(sys.argv[3])
        startTime = int(sys.argv[4])

        success, output = set_job_status_running(key, index, job_id, startTime)
        if success:
            print(f"tx_hash={output}")
        else:
            print(output)
    else:
        print("Please required related arguments {_key, index, startTime}.")
