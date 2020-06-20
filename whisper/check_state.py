#!/usr/bin/env python

import asyncio
import json
import os
import sys

from web3 import HTTPProvider, Web3

from config import env
from libs.whisper import log_loop
from utils import _colorize_traceback, log, read_json

web3 = Web3(HTTPProvider("http://localhost:8545"))
receiver_pub = "0x04d2a70458f4f3f821870d1979203f84e1cad44bd9cdc6f710eb513ef917c96a25188ff1d4b6b7e83e5168872ce958b29b4b8959f9118ddaf876f10227450540c2"


if __name__ == "__main__":
    if not os.path.isfile(env.WHISPER_INFO):
        log(f"{env.WHISPER_INFO} does not exist. Initializing...", "yellow")
        key_id = web3.geth.shh.newKeyPair()
        public_key = web3.geth.shh.getPublicKey(key_id)

        msg_filter = web3.geth.shh.new_message_filter(
            {"topic": env.WHISPER_TOPIC, "privateKeyID": key_id, "recipientPublicKey": public_key}
        )
        msg_filter.poll_interval = 600
        # make it equal with the live-time of the message
        filter_id = msg_filter.filter_id

        data = {}
        data["key_id"] = key_id
        data["public_key"] = public_key
        data["filter_id"] = filter_id

        with open("data.txt", "w") as outfile:
            json.dump(data, outfile)
    else:
        try:
            data = read_json(env.WHISPER_INFO)
        except:
            _colorize_traceback()

        key_id = data["key_id"]
        public_key = data["public_key"]
        if not web3.geth.shh.hasKeyPair(key_id):
            log("E: Whisper node's private key of a key pair did not match with the given ID", "red")
            sys.exit(1)

        filter_id = data["filter_id"]
        print(f"filter_id={filter_id}")

    print(public_key)
    filter_id = web3.geth.shh.new_message_filter(
        {"topic": env.WHISPER_TOPIC, "privateKeyID": key_id, "recipientPublicKey": public_key}
    )
    # msg_filter.poll_interval = 600
    # make it equal with the live-time of the message

    # Obtained from node_1 and assigned here.
    payloads = [web3.toHex(text=public_key), web3.toHex(text="2nd test message")]
    web3.geth.shh.post(
        {
            "powTarget": 2,  # 2.5
            "powTime": 5,  # 2
            "ttl": 60,
            "payload": payloads[0],
            "topic": env.WHISPER_TOPIC,
            "pubKey": receiver_pub,
        }
    )
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(asyncio.gather(log_loop(filter_id, 2, is_return=True, public_key=public_key)))
    finally:
        loop.close()
