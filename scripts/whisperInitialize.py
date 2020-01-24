#!/usr/bin/env python3

import json, sys, os.path
from web3.auto import w3
import asyncio
from web3 import Web3, HTTPProvider

web3 = Web3(HTTPProvider("http://localhost:8545"))

from os.path import expanduser

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
