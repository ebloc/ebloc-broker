#!/usr/bin/env python

from web3 import Web3, HTTPProvider
web3 = Web3(HTTPProvider('http://localhost:8545'))
from web3.shh import Shh
Shh.attach(web3, "shh")

import time, sys;

from hexbytes import (
    HexBytes,
)

# Obtained from node_1 and assigned here.
receiver_pub = '0x04560656f15856e3666c285f05d9f8fcc65b4771605f82392f1174e6fe26ecf923d0846f4371e18db1f187e78d02a1f0c36aab6006447e2905ddf36c1d3532fa82'

topic = '0x07678231'
payloads = [web3.toHex(text="test message :)"),
				web3.toHex(text="2nd test message")]

web3.shh.post({
        'powTarget': 2.5,
        'powTime': 2,
        'ttl': 60,
        'payload': payloads[0],
        'topic': topic,
        'pubKey': receiver_pub
})
