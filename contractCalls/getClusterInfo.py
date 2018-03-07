#!/usr/bin/env python -W ignore::DeprecationWarning

from __future__ import print_function
import os
from web3 import Web3
import json
from web3.providers.rpc import HTTPProvider

def ipfsBytesToString(ipfsID):
    val= web3.fromAscii(ipfsID);
    os.environ['val'] = '1220'+val[2:];
    return os.popen('node bs58.js decode $val').read().replace("\n", "");
    
web3 = Web3(HTTPProvider('http://localhost:8545'))

contractAddress='0xca9f407af4e36bfd4546a898d06c51cdc0da8a2a';
with open('abi.json', 'r') as abi_definition:
    abi = json.load(abi_definition)
    
eBlocBroker = web3.eth.contract(contractAddress, abi=abi);

cluster="0xc75497b304f42631d919f20db3e9b79dd59e88ff";

name, federationCloudId, miniLockId, coreLimit, coreMinutePrice, ipfsID = eBlocBroker.call().getClusterInfo(cluster);

ipfs=ipfsBytesToString(ipfsID)

print('Name: '+name);
print('Ipfs: '+ipfs)
