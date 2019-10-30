#!/usr/bin/env python3

import sys, os, traceback, lib
from imports import connect

def setJobStatus(_key, index, jobID, jobStateCode, startTime, eBlocBroker=None, w3=None):
    eBlocBroker, w3 = connect(eBlocBroker, w3)
    if eBlocBroker is None or w3 is None:
        return
        
    try:
        tx = eBlocBroker.functions.setJobStatus(_key, int(index), int(jobID), int(jobStateCode), int(startTime)).transact({"from": w3.toChecksumAddress(lib.PROVIDER_ID), "gas": 4500000})
    except Exception:
        return False, traceback.format_exc()

    return True, tx.hex()

if __name__ == '__main__':
    if len(sys.argv) == 6:
        _key         = str(sys.argv[1]) 
        index        = int(sys.argv[2])
        jobID        = int(sys.argv[3])
        jobStateCode = int(sys.argv[4]) 
        startTime    = int(sys.argv[5])

        status, result = setJobStatus(_key, index, jobID, jobStateCode, startTime)
        if status:
            print('tx_hash=' + result)
        else:
            print(result)
    else:
        print('Please required related arguments {_key, index, jobStateCode, startTime}.')

        
