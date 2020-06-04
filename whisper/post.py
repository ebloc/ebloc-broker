#!/usr/bin/env python

from web3 import HTTPProvider, Web3

web3 = Web3(HTTPProvider("http://localhost:8545"))

# Obtained from node_1 and assigned here.
receiver_pub = "0x04890c6c513fb3d2e375dee1f3fb8a35fb49e55382013cee152e106d6abbb9db1aa765cd61f59b9d078b9875aa38d31c5aaae826895f6ffea6de4645d170042fc7"

topic = "0x07678231"
payloads = [web3.toHex(text="test message :)"), web3.toHex(text="2nd test message")]

web3.geth.shh.post(
    {"powTarget": 2.5, "powTime": 2, "ttl": 60, "payload": payloads[0], "topic": topic, "pubKey": receiver_pub,}
)
