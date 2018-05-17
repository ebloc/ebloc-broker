#!/usr/bin/env python

import os, json, sys, time
from web3 import Web3
from web3.providers.rpc import HTTPProvider
sys.path.insert(1, os.path.join(sys.path[0], '..')); import constants
os.chdir(sys.path[0]);

def ipfsBytesToString(ipfsID):
    val= web3.fromAscii(ipfsID);
    os.environ['val'] = '1220'+val[2:];
    return os.popen('node bs58.js decode $val').read().replace("\n", "");

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

print(eBlocBroker.functions.getOwner().call());
