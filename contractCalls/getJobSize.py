#!/usr/bin/env python

import os, json, sys, time
from web3 import Web3
from web3.providers.rpc import HTTPProvider
sys.path.insert(1, os.path.join(sys.path[0], '..')); import constants
os.chdir(sys.path[0]);

web3 = Web3(HTTPProvider('http://localhost:' + str(constants.RPC_PORT)))

if not web3.isConnected():
    print('notconnected')
    sys.exit()

fileAddr = open("address.json", "r")
contractAddress = fileAddr.read().replace("\n", "")

with open('abi.json', 'r') as abi_definition:
    abi = json.load(abi_definition)

contractAddress = web3.toChecksumAddress(contractAddress);
eBlocBroker = web3.eth.contract(contractAddress, abi=abi);

if __name__ == '__main__': #{
    if len(sys.argv) == 3:
        clusterAddress = str(sys.argv[1]);
        jobKey         = str(sys.argv[2]);
    else:
        clusterAddress = "0x75a4c787c5c18c587b284a904165ff06a269b48c";
        jobKey         = "QmRsaBEGcqxQcJbBxCi1LN9iz5bDAGDWR6Hx7ZvWqgqmdR";

    clusterAddress = web3.toChecksumAddress(clusterAddress);
    print(eBlocBroker.call().getJobSize(clusterAddress, jobKey));
#}
