#!/usr/bin/env python3

import sys

from config import logging  # noqa: F401
from imports import connect
from settings import init_env
from utils import _colorize_traceback


def set_job_status_running(_key, index, job_id, startTime):
    eBlocBroker, w3 = connect()
    env = init_env()

    try:
        tx = eBlocBroker.functions.setJobStatusRunning(_key, int(index), int(job_id), int(startTime)).transact(
            {"from": w3.toChecksumAddress(env.PROVIDER_ID), "gas": 4500000}
        )
        return tx.hex()
    except Exception:
        logging.info(_colorize_traceback())
        raise


if __name__ == "__main__":
    if len(sys.argv) == 5:
        key = str(sys.argv[1])
        index = int(sys.argv[2])
        job_id = int(sys.argv[3])
        startTime = int(sys.argv[4])
    else:
        print("Please required related arguments {_key, index, startTime}")
        sys.exit(1)

    try:
        tx_hash = set_job_status_running(key, index, job_id, startTime)
        print(f"tx_hash={tx_hash}")
    except:
        print(_colorize_traceback())
        sys.exit(1)
