#!/usr/bin/env python -W ignore::DeprecationWarning

import os, json, sys, time
from web3 import Web3
from web3.providers.rpc import HTTPProvider
sys.path.insert(1, os.path.join(sys.path[0], '..')); import constants
os.chdir(sys.path[0]);

os.chdir(sys.path[0]);    
web3 = Web3(HTTPProvider('http://localhost:' + str(constants.RPC_PORT)))
print(str(web3.eth.blockNumber).replace("\n", ""));
    
