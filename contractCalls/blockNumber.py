#!/usr/bin/env python -W ignore::DeprecationWarning

from __future__ import print_function
import os, sys
from web3 import Web3
import json
from web3.providers.rpc import HTTPProvider

os.chdir(sys.path[0]);    
web3 = Web3(HTTPProvider('http://localhost:8545'))
print(str(web3.eth.blockNumber).replace("\n", ""));
    
