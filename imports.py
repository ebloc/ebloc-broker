#!/usr/bin/env python3

import os, json, sys, time
from web3 import Web3
from web3.providers.rpc import HTTPProvider
from web3 import Web3, IPCProvider
from os.path import expanduser
import lib
home = expanduser("~")  

def getWeb3():
    if lib.POA_CHAIN == 0:
        '''
		* Note that you should create only one RPC Provider per process,
		* as it recycles underlying TCP/IP network connections between
		*  your process and Ethereum node
        '''
        web3 = Web3(HTTPProvider('http://localhost:' + str(lib.RPC_PORT)))
        from web3.shh import Shh
        Shh.attach(web3, "shh")
    else:
        web3 = Web3(IPCProvider('/private/geth.ipc')) 
        from web3.middleware import geth_poa_middleware
        # inject the poa compatibility middleware to the innermost layer
        web3.middleware_stack.inject(geth_poa_middleware, layer=0)
        from web3.shh import Shh
        Shh.attach(web3, 'shh')
    if not web3.isConnected():
        lib.log('Error: If web3 is not connected please run the following: sudo chown -R $(whoami) /private/geth.ipc', 'red')
        return False   
    return web3 

def connectEblocBroker(web3=None):
    if web3 is None:
        web3 = getWeb3()
        if not web3:
            return False

    contract = json.loads(open(home + '/eBlocBroker/contractCalls/contract.json').read())    
    contractAddress = contract['address']
    
    with open(home + '/eBlocBroker/contractCalls/abi.json', 'r') as abi_definition:
        abi = json.load(abi_definition)

    contractAddress = web3.toChecksumAddress(contractAddress) 
    eBlocBroker     = web3.eth.contract(contractAddress, abi=abi)
    return eBlocBroker 

if __name__ == '__main__': 
    eBlocBroker = connectEblocBroker() 

# [Errno 111] Connection refused => web3 is not connected (class.name: ConnectionRefusedError)
# Exception: web3.exceptions.BadFunctionCallOutput => wrong mapping input is give (class.name: BadFunctionCallOutput)
