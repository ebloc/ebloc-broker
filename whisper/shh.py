#!/usr/bin/env python

from web3 import Web3, HTTPProvider
web3 = Web3(HTTPProvider('http://localhost:8545'))
from web3.shh import Shh
Shh.attach(web3, "shh")

import time, sys;

from hexbytes import (
    HexBytes,
)

print ("web3 =", web3.version.api)

sender = web3.shh.newKeyPair()
sender_pub = web3.shh.getPublicKey(sender)

receiver = web3.shh.newKeyPair()
receiver_pub = web3.shh.getPublicKey(receiver)

receiver_pub='0x047c2dd62760846134f5ddcb80ad7e0345fa7b247feb517c1595b4d14254c14390cf5a95f383c743e5bad0ba85a626ee2ea8361a808e6efa1002ce31cea6eb4e94';

topic = '0x13370000'
payloads = [web3.toHex(text="test message :)"), web3.toHex(text="2nd test message")]

shh_filter = web3.shh.newMessageFilter({
        'privateKeyID': receiver,
        'topics': [topic]
})

web3.shh.post({
        'powTarget': 2.5,
        'ttl': 60,
        'powTime': 2,
        'payload': payloads[0],
        'pubKey': receiver_pub
})
time.sleep(1)

web3.shh.post({
        'powTarget': 2.5,
        'ttl': 60,
        'powTime': 2,
        'payload': payloads[1],
        'topic': topic,
        'pubKey': receiver_pub
})
