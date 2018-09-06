#!/usr/bin/env python

import os, json, sys, time
from web3 import Web3
from web3.providers.rpc import HTTPProvider
from web3 import Web3, IPCProvider
from os.path import expanduser
import lib
home = expanduser("~")  

def getWeb3(): #{
    if lib.POA_CHAIN == 0:
	# Note that you should create only one RPCProvider per process,
	# as it recycles underlying TCP/IP network connections between
	# your process and Ethereum node
        web3 = Web3(HTTPProvider('http://localhost:' + str(lib.RPC_PORT)))
    else: #{
        web3 = Web3(IPCProvider(home + '/eblocPOA/private/geth.ipc')) 
        from web3.middleware import geth_poa_middleware
        # inject the poa compatibility middleware to the innermost layer
        web3.middleware_stack.inject(geth_poa_middleware, layer=0)
    #}

    if not web3.isConnected(): #{
        print('notconnected') 
        sys.exit() 
    #}
    return web3 
#}

def connectEblocBroker(web3=None): #{
    if web3 == None:
        web3 = getWeb3()         
    fileAddr = open(home + '/eBlocBroker/contractCalls/address.json', "r")
    contractAddress = fileAddr.read().replace("\n", "")

    with open(home + '/eBlocBroker/contractCalls/abi.json', 'r') as abi_definition:
        abi = json.load(abi_definition)

    contractAddress = web3.toChecksumAddress(contractAddress) 
    eBlocBroker     = web3.eth.contract(contractAddress, abi=abi) 
    return eBlocBroker 
#}

if __name__ == '__main__': #{
    eBlocBroker = connectEblocBroker() 
#}
