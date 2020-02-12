#!/usr/bin/env python

import sys
import time

from hexbytes import HexBytes
from web3 import HTTPProvider, Web3
from web3.shh import Shh

web3 = Web3(HTTPProvider("http://localhost:8545"))

Shh.attach(web3, "shh")


loadFlag = 0

if loadFlag == 1:
    privateKey = "0x5fc212a0774add56f4a32b59a1cf6100ae0ef8fe1481c1ab7d011796d1e53320"
    kId = web3.shh.addPrivateKey(privateKey)
else:
    kId = web3.shh.newKeyPair()

receiver_priv = web3.shh.getPrivateKey(kId)
receiver_pub = web3.shh.getPublicKey(kId)

print("receiverPrivK: " + receiver_priv)
print("receiverPubK: " + receiver_pub)

myFilter = web3.shh.newMessageFilter({"topic": "0x07678231", "privateKeyID": kId})
print("FilterID: " + myFilter.filter_id)

input("Press Enter to continue...")

received_messages = []
received_messages = myFilter.get_new_entries()
print(len(received_messages))

print(web3.shh.info.memory)
print(received_messages[0])
