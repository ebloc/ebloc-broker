#!/usr/bin/env python3


import json

from web3 import HTTPProvider, Web3

from config import env

w3 = Web3(HTTPProvider("http://localhost:8545"))


print("Initializing...")
key_id = w3.geth.shh.newKeyPair()  # generates a new public and private key pair for message decryption and encryption.
public_key = w3.geth.shh.getPublicKey(key_id)
filter_id = w3.geth.shh.new_message_filter(
    {"topic": env.WHISPER_TOPIC, "privateKeyID": key_id, "recipientPublicKey": public_key}
)

data = {}
data["key_id"] = key_id
data["public_key"] = public_key
data["filter_id"] = filter_id

with open(env.WHISPER_INFO, "w") as outfile:
    json.dump(data, outfile)

print(f"You can access your whisper info from {env.WHISPER_INFO}")
