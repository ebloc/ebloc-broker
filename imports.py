#!/usr/bin/env python3

import os, json, sys, time
import logging
from web3 import Web3
from web3.providers.rpc import HTTPProvider
from web3 import Web3, IPCProvider
from os.path import expanduser
import lib
home = expanduser("~")  
logger = logging.Logger('catch_all')

class Network(object):
    def __init__(self):
        # Let's add some data to the [instance of the] class.
        self.eBlocBroker = None
        self.w3 = None
        self.oc = None
        
def connect(eBlocBroker, w3):
    if eBlocBroker is not None and w3 is not None:
        return eBlocBroker, w3
    
    if w3 is None:
        try:
            w3 = getWeb3()
        except Exception as e:
            logger.error('Failed to connect web3: ' + str(e))
            return None, None

        if not w3:
            return None, None

    if eBlocBroker is None :
        try:
            eBlocBroker = connectEblocBroker(w3)
        except Exception as e:
            logger.error('Failed to connect eBlocBroker: ' + str(e))
            return None, None
        
    return eBlocBroker, w3

def getWeb3():
    if lib.POA_CHAIN == 0:
        '''
		* Note that you should create only one RPC Provider per process,
		* as it recycles underlying TCP/IP network connections between
		*  your process and Ethereum node
        '''
        w3 = Web3(HTTPProvider('http://localhost:' + str(lib.RPC_PORT)))
        from web3.shh import Shh
        Shh.attach(web3, "shh")
    else:
        w3 = Web3(IPCProvider('/private/geth.ipc')) 
        from web3.middleware import geth_poa_middleware
        # inject the poa compatibility middleware to the innermost layer
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        # from web3.shh import Shh
        # Shh.attach(web3, 'shh')
    if not w3.isConnected():
        lib.log('Error: If web3 is not connected please run the following: sudo chown -R $(whoami) /private/geth.ipc', 'red')
        return False
    
    return w3 

def connectEblocBroker(w3=None):
    if w3 is None:
        w3 = getWeb3()
        if not w3:
            return False

    contract = json.loads(open(home + '/eBlocBroker/contractCalls/contract.json').read())    
    contractAddress = contract['address']
    
    with open(home + '/eBlocBroker/contractCalls/abi.json', 'r') as abi_definition:
        abi = json.load(abi_definition)

    contractAddress = w3.toChecksumAddress(contractAddress) 
    eBlocBroker     = w3.eth.contract(contractAddress, abi=abi)
    return eBlocBroker 

if __name__ == '__main__': 
    eBlocBroker = connectEblocBroker() 

# [Errno 111] Connection refused => w3 is not connected (class.name: ConnectionRefusedError)
# Exception: w3.exceptions.BadFunctionCallOutput => wrong mapping input is give (class.name: BadFunctionCallOutput)
