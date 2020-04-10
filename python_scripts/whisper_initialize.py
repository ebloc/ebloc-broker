#!/usr/bin/env python3


import json
from os.path import expanduser

from web3 import HTTPProvider, Web3

w3 = Web3(HTTPProvider("http://localhost:8545"))

home = expanduser("~")

topic = "0x07678231"

print("Initializing...")
k_id = w3.geth.shh.newKeyPair()  # generates a new public and private key pair for message decryption and encryption.
public_key = w3.geth.shh.getPublicKey(k_id)
filter_id = w3.geth.shh.newMessageFilter({"topic": topic, "privateKeyID": k_id, "recipientPublicKey": public_key})

data = {}
data["kId"] = k_id
data["publicKey"] = public_key
data["filter_id"] = filter_id

with open(home + "/.eBlocBroker/whisperInfo.txt", "w") as outfile:
    json.dump(data, outfile)

print("Done.")
print("You can access your whisper info from $HOME/.eBlocBroker/whisperInfo.txt")
