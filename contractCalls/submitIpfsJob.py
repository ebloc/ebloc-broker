#!/usr/bin/env python

import os, sys
from web3 import Web3
import json
from web3.providers.rpc import HTTPProvider

os.chdir(sys.path[0]);

# Note that you should create only one RPCProvider per process,
# as it recycles underlying TCP/IP network connections between
# your process and Ethereum node
web3 = Web3(HTTPProvider('http://localhost:8545'))

fileAddr = open("address.json", "r")
contractAddress = fileAddr.read().replace("\n", "")

with open('abi.json', 'r') as abi_definition:
    abi = json.load(abi_definition)

contractAddress = web3.toChecksumAddress(contractAddress);
eBlocBroker = web3.eth.contract(contractAddress, abi=abi);
# USER Inputs----------------------------------------------------------------
account          = web3.eth.accounts[1]; # Sender's Ethereum Account
clusterAddress   = "0x6af0204187a93710317542d383a1b547fa42e705"; # clusterAddress that you would like to submit.
ipfsHash         = "QmefdYEriRiSbeVqGvLx15DKh4WqSMVL8nT4BwvsgVZ7a5"
coreNumber       = 128;
jobDescription   = "Science"
coreNum          = 1; 
coreGasDay       = 0;
coreGasHour      = 0;
coreGasMin       = 10;
storageType      = 0;
# ----------------------------------------------------------------------------
name, federationCloudId, miniLockId, coreLimit, coreMinutePrice, ipfsID = eBlocBroker.call().getClusterInfo(clusterAddress);
coreMinuteGas    = coreGasMin + coreGasHour * 60 + coreGasDay * 1440;
myMiniLockId     = "";

if(coreNum <= coreLimit and len(jobDescription) < 128 and len(ipfsHash) == 46):
    tx=eBlocBroker.transact({"from":account, "value": coreNum * coreMinutePrice * coreMinuteGas, "gas": 4500000}).submitJob(clusterAddress, ipfsHash, coreNum, jobDescription, coreMinuteGas, storageType, myMiniLockId);
    print(tx);
