#!/usr/bin/env python3

import sys, os, lib

def setJobStatus(_key, index, jobStateCode, startTime, eBlocBroker=None, web3=None):
    if eBlocBroker is None and web3 is None:
        from imports import connectEblocBroker, getWeb3
        web3           = getWeb3()
        eBlocBroker    = connectEblocBroker(web3)

    tx = eBlocBroker.transact({"from": web3.toChecksumAddress(lib.PROVIDER_ID), "gas": 4500000}).setJobStatus(_key, int(index), int(jobStateCode), int(startTime)) 
    return tx.hex()

if __name__ == '__main__':
    if len(sys.argv) == 5:
        _key         = str(sys.argv[1]) 
        index        = int(sys.argv[2]) 
        jobStateCode = int(sys.argv[3]) 
        startTime    = int(sys.argv[4])
        
        print(setJobStatus(_key, index, jobStateCode, startTime))
    else:
        print('Please required related arguments {_key, index, jobStateCode, startTime}.')

        
