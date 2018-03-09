#!/usr/bin/env python

from __future__ import print_function
from web3 import Web3
import json
from web3.providers.rpc import HTTPProvider

web3 = Web3(HTTPProvider('http://localhost:8545'))

contractAddress='0xca9f407af4e36bfd4546a898d06c51cdc0da8a2a';
with open('abi.json', 'r') as abi_definition:
    abi = json.load(abi_definition)
    
eBlocBroker = web3.eth.contract(contractAddress, abi=abi);

clusterAddress="0xda1e61e853bb8d63b1426295f59cb45a34425b63";

print(eBlocBroker.call().isClusterExist(clusterAddress));
