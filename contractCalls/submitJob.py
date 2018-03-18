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
    if(len(sys.argv) == 10):
        clusterAddress = str(sys.argv[1]);
        blockReadFrom, coreNumber, pricePerMin = eBlocBroker.call().getClusterInfo(clusterAddress);
        jobKey         = str(sys.argv[2]);
        coreNum        = int(sys.argv[3]);
        coreGasDay     = int(sys.argv[4]);
        coreGasHour    = int(sys.argv[5]);
        coreGasMin     = int(sys.argv[6]);
        jobDescription = str(sys.argv[7]);
        storageType    = int(sys.argv[8]);
        myMiniLockId   = str(sys.argv[9]);
    else:
        # USER Inputs----------------------------------------------------------------
        clusterAddress = "0x6af0204187a93710317542d383a1b547fa42e705";
        blockReadFrom, coreNumber, pricePerMin = eBlocBroker.call().getClusterInfo(clusterAddress);
        jobKey         = "3d8e2dc2-b855-1036-807f-9dbd8c6b1579=folderName";
        coreNum        = 1;
        coreGasDay     = 0;
        coreGasHour    = 0;
        coreGasMin     = 1;
        jobDescription = "Science";
        storageType    = 1;
        myMiniLockId   = "";
        # ----------------------------------------------------------------------------        
    coreMinuteGas = coreGasMin + coreGasHour * 60 + coreGasDay * 1440;
    msgValue = coreNum * pricePerMin * coreMinuteGas;
    gasLimit = 3000000;

    if (coreNum <= coreNumber and len(jobDescription) < 128 ):
        tx=eBlocBroker.transact({"from": web3.eth.accounts[0], "value": msgValue, "gas": gasLimit}).submitJob(clusterAddress, jobKey, coreNum, jobDescription, coreMinuteGas, storageType, myMiniLockId);
        print(tx);

#}


