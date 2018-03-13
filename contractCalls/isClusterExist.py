#!/usr/bin/env python

from __future__ import print_function
from web3 import Web3
import json, sys, os
from web3.providers.rpc import HTTPProvider

os.chdir(sys.path[0]);

web3 = Web3(HTTPProvider('http://localhost:8545'))

fileAddr = open("address.json", "r")
contractAddress = fileAddr.read().replace("\n", "")

with open('abi.json', 'r') as abi_definition:
    abi = json.load(abi_definition)
    
eBlocBroker = web3.eth.contract(contractAddress, abi=abi);

if __name__ == '__main__': #{
    if(len(sys.argv) == 2):
        clusterAddress = str(sys.argv[1]);
    else:
        clusterAddress = "0xc75497b304f42631d919f20db3e9b79dd59e88ff";
        
    print(str(eBlocBroker.call().isClusterExist(clusterAddress)).rstrip('\n'));
#}
