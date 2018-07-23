#!/usr/bin/env python

import os, json, sys, time
from web3 import Web3
from web3.providers.rpc import HTTPProvider
from web3 import Web3, IPCProvider 
sys.path.insert(1, os.path.join(sys.path[0], '..')); import constants
os.chdir(sys.path[0]);

if constants.POA_CHAIN == 0:
    # Note that you should create only one RPCProvider per process,
    # as it recycles underlying TCP/IP network connections between
    # your process and Ethereum node
    web3 = Web3(HTTPProvider('http://localhost:' + str(constants.RPC_PORT)))
else: #{
    web3 = Web3(IPCProvider('/home/alper/eblocPOA/private/geth.ipc'));
    from web3.middleware import geth_poa_middleware
    # inject the poa compatibility middleware to the innermost layer
    web3.middleware_stack.inject(geth_poa_middleware, layer=0)
#}

if not web3.isConnected(): #{
    print('notconnected');
    sys.exit();
#}

fileAddr = open("address.json", "r")
contractAddress = fileAddr.read().replace("\n", "")

with open('abi.json', 'r') as abi_definition:
    abi = json.load(abi_definition)

contractAddress = web3.toChecksumAddress(contractAddress);
eBlocBroker     = web3.eth.contract(contractAddress, abi=abi);

