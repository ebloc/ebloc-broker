#!/usr/bin/env python

import os, json, sys
from web3 import Web3
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

eBlocBroker = web3.eth.contract(contractAddress, abi=abi);

if __name__ == '__main__': #{
    if(len(sys.argv) == 8):
        clusterAddress = str(sys.argv[1]);
        blockReadFrom, coreNumber, pricePerMin = eBlocBroker.call().getClusterInfo(clusterAddress);
        jobKey         = str(sys.argv[2]);
        coreNum        = int(sys.argv[3]);
        jobDescription = str(sys.argv[4]);
        coreMinuteGas  = int(sys.argv[5]);
        storageType    = int(sys.argv[6]);
        myMiniLockId   = str(sys.argv[7]);
    else:
        print(len(sys.argv))
        sys.exit()
        # ----------------------------------------------------------------------------
    msgValue = coreNum * pricePerMin * coreMinuteGas;
    gasLimit = 3000000;

    if (coreNum <= coreNumber and len(jobDescription) < 128 ):
        tx=eBlocBroker.transact({"from": web3.eth.accounts[2], "value": msgValue, "gas": gasLimit}).submitJob(clusterAddress, jobKey, coreNum, jobDescription,
coreMinuteGas, storageType, myMiniLockId);
        print(tx);
#}
