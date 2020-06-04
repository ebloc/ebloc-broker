#!/usr/bin/env python3

import sys

from config import env, logging  # noqa: F401
from eblocbroker.Contract import Contract
from utils import _colorize_traceback

if __name__ == "__main__":
    c = Contract()

    if len(sys.argv) == 5:
        key = str(sys.argv[1])
        index = int(sys.argv[2])
        job_id = int(sys.argv[3])
        startTime = int(sys.argv[4])
    else:
        print("Please required related arguments {_key, index, startTime}")
        sys.exit(1)

    try:
        tx_hash = c.set_job_status_running(key, index, job_id, startTime)
        print(f"tx_hash={tx_hash}")
    except:
        _colorize_traceback()
        sys.exit(1)
