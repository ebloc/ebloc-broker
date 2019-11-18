#!/usr/bin/env python3

import sys


def getJobSize(provider, key, eBlocBroker=None, web3=None):
    if eBlocBroker is None and web3 is None:
        from imports import connectEblocBroker, getWeb3
        web3 = getWeb3()
        eBlocBroker = connectEblocBroker(web3)

    provider = web3.toChecksumAddress(provider) 
    return eBlocBroker.call().getJobSize(provider, key)


if __name__ == '__main__':
    if len(sys.argv) == 3:
        provider = str(sys.argv[1]) 
        key = str(sys.argv[2]) 
    else:
        provider = "0x4e4a0750350796164d8defc442a712b7557bf282" 
        key = "QmRsaBEGcqxQcJbBxCi1LN9iz5bDAGDWR6Hx7ZvWqgqmdR" 

    print(getJobSize(provider, key))
