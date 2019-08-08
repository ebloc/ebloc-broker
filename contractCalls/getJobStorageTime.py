#!/usr/bin/env python3

import sys

def getJobStorageTime(providerAddress, sourceCodeHash, eBlocBroker=None, web3=None):
    if eBlocBroker is None and web3 is None:
        import os
        from imports import connectEblocBroker, getWeb3
        web3           = getWeb3()
        eBlocBroker    = connectEblocBroker(web3)

    providerAddress = web3.toChecksumAddress(providerAddress)
    ret = eBlocBroker.call().getJobStorageTime(providerAddress, sourceCodeHash)
    return ret[0], ret[1]
    
if __name__ == '__main__':
    if len(sys.argv) == 3:
        providerAddress = str(sys.argv[1]) 
        sourceCodeHash = str(sys.argv[2]) 
    else:
        providerAddress = '0x57b60037b82154ec7149142c606ba024fbb0f991' 
        sourceCodeHash = 'acfd2fd8a1e9ccf031db0a93a861f6eb'

    receivedBlockNum, storageTime = getJobStorageTime(providerAddress, sourceCodeHash)
    print('receivedBlockNum=' + str(receivedBlockNum) + '; ' +
          'storageTime='      + str(storageTime)  + '; ' +
          'endBlockTime='     + str(receivedBlockNum + storageTime * 240))
