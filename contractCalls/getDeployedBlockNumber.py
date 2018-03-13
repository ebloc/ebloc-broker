#!/usr/bin/env python -W ignore::DeprecationWarning

from __future__ import print_function
import os, sys
from web3 import Web3
import json
from web3.providers.rpc import HTTPProvider

os.chdir(sys.path[0]);

def ipfsBytesToString(ipfsID):
    val= web3.fromAscii(ipfsID);
    os.environ['val'] = '1220'+val[2:];
    return os.popen('node bs58.js decode $val').read().replace("\n", "");
    
web3 = Web3(HTTPProvider('http://localhost:8545'))

fileAddr = open("address.json", "r")
contractAddress = fileAddr.read().replace("\n", "")

with open('abi.json', 'r') as abi_definition:
    abi = json.load(abi_definition)
    
eBlocBroker = web3.eth.contract(contractAddress, abi=abi);
print(eBlocBroker.call().getDeployedBlockNumber());
