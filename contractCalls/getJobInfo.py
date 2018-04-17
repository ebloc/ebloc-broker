#!/usr/bin/env python

import os, json, sys, time
from web3 import Web3
from web3.providers.rpc import HTTPProvider
sys.path.insert(1, os.path.join(sys.path[0], '..')); import constants
os.chdir(sys.path[0]);
os.system('#!/bin/bash source $HOME/.venv-py3/bin/activate')

web3 = Web3(HTTPProvider('http://localhost:' + str(constants.RPC_PORT)))

fileAddr = open("address.json", "r")
contractAddress = fileAddr.read().replace("\n", "")

with open('abi.json', 'r') as abi_definition:
    abi = json.load(abi_definition)

contractAddress = web3.toChecksumAddress(contractAddress);
eBlocBroker = web3.eth.contract(contractAddress, abi=abi);

if __name__ == '__main__': #{
    if(len(sys.argv) == 4):
        clusterAddress = str(sys.argv[1]);
        jobKey         = str(sys.argv[2]);
        index          = int(sys.argv[3]);
    else:
        clusterAddress = "0x6af0204187a93710317542d383a1b547fa42e705";
        jobKey         = "3d8e2dc2-b855-1036-807f-9dbd8c6b1579=117649886378445811229351254502963812811";
        index          = 3;
        #jobKey          = "QmTXyUrHxkf2m85W6Sy6VAMBuZyZAuSDQAbjSgDcLLnEdW";
        #index           = 4;
    clusterAddress = web3.toChecksumAddress(clusterAddress);
    print(eBlocBroker.call().getJobInfo(clusterAddress, jobKey, index));
    # print(eBlocBroker.functions.getJobInfo(clusterAddress, jobKey, index).call());
#}
