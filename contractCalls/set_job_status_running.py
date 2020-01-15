#!/usr/bin/env python3

import sys
import traceback
import lib
from imports import connect


def set_job_status_running(_key, index, jobID, startTime, eBlocBroker=None, w3=None):
    eBlocBroker, w3 = connect(eBlocBroker, w3)
    if eBlocBroker is None or w3 is None:
        return
        
    try:
        tx = eBlocBroker.functions.setJobStatusRunning(_key, int(index), int(jobID), int(startTime)).transact({"from": w3.toChecksumAddress(lib.PROVIDER_ID), "gas": 4500000})
    except Exception:
        return False, traceback.format_exc()

    return True, tx.hex()


if __name__ == '__main__':
    if len(sys.argv) == 5:
        key = str(sys.argv[1]) 
        index = int(sys.argv[2])
        jobID = int(sys.argv[3])
        startTime = int(sys.argv[4])

        status, result = set_job_status_running(key, index, jobID, startTime)
        if status:
            print('tx_hash=' + result)
        else:
            print(result)
    else:
        print('Please required related arguments {_key, index, startTime}.')
