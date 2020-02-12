#!/usr/bin/env python3

import asyncio
import json
import os.path
import sys
from os.path import expanduser

from web3 import HTTPProvider, Web3
from web3.auto import w3

web3 = Web3(HTTPProvider("http://localhost:8545"))


home = expanduser("~")

topic = "0x07678231"

print("Initializing...")
kId = web3.geth.shh.newKeyPair()  # Generates a new public and private key pair for message decryption and encryption.
publicKey = web3.geth.shh.getPublicKey(kId)
filter_id = web3.geth.shh.newMessageFilter({"topic": topic, "privateKeyID": kId, "recipientPublicKey": publicKey})

data = {}
data["kId"] = kId
data["publicKey"] = publicKey
data["filter_id"] = filter_id

with open(home + "/.eBlocBroker/whisperInfo.txt", "w") as outfile:
    json.dump(data, outfile)

print("Done.")
print("You can access your whisper info from $HOME/.eBlocBroker/whisperInfo.txt")
