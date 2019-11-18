#!/usr/bin/env python3 -W ignore::DeprecationWarning

from __future__ import print_function
import os, sys
from web3 import Web3
from web3.providers.rpc import HTTPProvider


os.chdir(sys.path[0])


def ipfsBytesToString(ipfsID):
    val = web3.fromAscii(ipfsID) 
    os.environ['val'] = '1220' + val[2:] 
    return os.popen('node bs58.js decode $val').read().replace("\n", "") 


web3 = Web3(HTTPProvider('http://localhost:8545'))

print(web3.personal)
