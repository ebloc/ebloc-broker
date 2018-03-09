#!/usr/bin/env python

import os, json
from web3 import Web3
from web3.providers.rpc import HTTPProvider

# Note that you should create only one RPCProvider per process,
# as it recycles underlying TCP/IP network connections between
# your process and Ethereum node
web3 = Web3(HTTPProvider('http://localhost:8545'))

contractAddress='0xca9f407af4e36bfd4546a898d06c51cdc0da8a2a';
with open('abi.json', 'r') as abi_definition:
    abi = json.load(abi_definition)
    
eBlocBroker = web3.eth.contract(contractAddress, abi=abi);

# USER Inputs----------------------------------------------------------------
clusterAddress = "0xc75497b304f42631d919f20db3e9b79dd59e88ff";
name, federationCloudId, miniLockId, coreLimit, pricePerMin, ipfsID = eBlocBroker.call().getClusterInfo(clusterAddress);
jobKey         = "3d8e2dc2-b855-1036-807f-9dbd8c6b1579=folderName";
coreNum        = 1;
coreGasDay     = 0;
coreGasHour    = 0;
coreGasMin     = 10;
jobDescription = "Science";
storageType    = 1;
myMiniLockId   = "";
# ----------------------------------------------------------------------------
coreMinuteGas = coreGasMin + coreGasHour * 60 + coreGasDay * 1440;
msgValue = coreNum * pricePerMin * coreMinuteGas;
gasLimit = 3000000;

if (coreNum <= coreLimit and len(jobDescription) < 128 ):
    tx=eBlocBroker.transact({"from": web3.eth.accounts[0], "value": msgValue, "gas": gasLimit}).submitJob(clusterAddress, jobKey, coreNum, jobDescription, coreMinuteGas, storageType, myMiniLockId);
    print(tx);        
