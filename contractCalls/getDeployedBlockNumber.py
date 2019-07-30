#!/usr/bin/env python3

import sys, json
from os.path import expanduser
home = expanduser("~")

def getDeployedBlockNumber(web3=None):
    from imports import connectEblocBroker, getWeb3
    web3 = getWeb3()
    if not web3:
        return False
    
    contract = json.loads(open(home + '/eBlocBroker/contractCalls/contract.json').read())
    return web3.eth.getTransaction(contract["txHash"]).blockNumber

if __name__ == '__main__':
    print(getDeployedBlockNumber())
