#!/usr/bin/env python

import sys
import time

from hexbytes import HexBytes
from web3 import HTTPProvider, Web3

web3 = Web3(HTTPProvider("http://localhost:8545"))


# Obtained from node_1 and assigned here.
receiver_pub = "0x04e2947a2c78ce17c2de5c266a1db90360b4a975b1c63b9a43b6c65cae570e40a9db2c31c0ed1be8bbe197d1029c30e58fa699d4a8936e418c9c6a9a489e100793"

topic = "0x07678231"
payloads = [web3.toHex(text="test message :)"), web3.toHex(text="2nd test message")]

web3.geth.shh.post(
    {"powTarget": 2.5, "powTime": 2, "ttl": 60, "payload": payloads[0], "topic": topic, "pubKey": receiver_pub,}
)
