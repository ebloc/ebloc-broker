#!/usr/bin/env python

from web3 import Web3, HTTPProvider
web3 = Web3(HTTPProvider('http://localhost:8545'))
from web3.shh import Shh
Shh.attach(web3, "shh")

import time, sys;

from hexbytes import (
    HexBytes,
)

loadFlag = 1

if loadFlag == 1:
    privateKey = '0x5fc212a0774add56f4a32b59a1cf6100ae0ef8fe1481c1ab7d011796d1e53320' 
    kId = web3.shh.addPrivateKey(privateKey)
else:
    kId          = web3.shh.newKeyPair()

receiver_pub = web3.shh.getPublicKey(kId)
print('receiverPubK: ' + receiver_pub);

myFilter = web3.shh.newMessageFilter({'topic': '0x07678231', 'privateKeyID': kId})
print('FilterID: ' + myFilter.filter_id)

input("Press Enter to continue...");

received_messages = [];
received_messages = myFilter.get_new_entries()
print(len(received_messages)) 

print(received_messages[0])
print(web3.shh.info.memory)  
