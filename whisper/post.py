#!/usr/bin/env python

from web3 import HTTPProvider, Web3

from config import env

web3 = Web3(HTTPProvider("http://localhost:8545"))

# Obtained from the node_1 and assigned here
receiver_pub = "0x04d2a70458f4f3f821870d1979203f84e1cad44bd9cdc6f710eb513ef917c96a25188ff1d4b6b7e83e5168872ce958b29b4b8959f9118ddaf876f10227450540c2"

payloads = [web3.toHex(text="test message :)"), web3.toHex(text="2nd test message")]

# target_peer = "40760b97c4ff1aa2d6fb13b99747db3cd19995828776ce208fd5c4bf5caac7ba"
web3.geth.shh.post(
    {
        "powTarget": 2.5,
        "powTime": 2,
        "ttl": 60,
        "payload": payloads[0],
        "topic": env.WHISPER_TOPIC,
        "pubKey": receiver_pub,
    }
)
