#!/usr/bin/env python3


import json

from web3 import HTTPProvider, Web3

from config import env
from utils import json_pretty, printc

w3 = Web3(HTTPProvider("http://localhost:8545"))


print("Initializing...")
# generates a new public and private key pair for message decryption and
# encryption
key_id = w3.geth.shh.newKeyPair()
public_key = w3.geth.shh.getPublicKey(key_id)
filter_id = w3.geth.shh.new_message_filter(
    {"topic": env.WHISPER_TOPIC, "privateKeyID": key_id, "recipientPublicKey": public_key}
)

data = {}
data["key_id"] = key_id
data["public_key"] = public_key
data["filter_id"] = filter_id

json_pretty(data)  # prints data
with open(env.WHISPER_INFO, "w") as outfile:
    json.dump(data, outfile)

printc(f"==> You can access your whisper info from {env.WHISPER_INFO}", "green")
