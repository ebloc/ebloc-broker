#!/usr/bin/env python

import os, json, sys, time
from web3 import Web3
from web3.providers.rpc import HTTPProvider
sys.path.insert(1, os.path.join(sys.path[0], '..')); import constants
os.chdir(sys.path[0]);

# Note that you should create only one RPCProvider per process,
# as it recycles underlying TCP/IP network connections between
# your process and Ethereum node
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

jobKey    = str(sys.argv[1]);
index     = int(sys.argv[2]);
stateID   = int(sys.argv[3]);
startTime = int(sys.argv[4]);

tx = eBlocBroker.transact({"from":web3.toChecksumAddress(constants.CLUSTER_ID), "gas": 4500000}).setJobStatus(jobKey, index, stateID, startTime);
print(tx.hex());
