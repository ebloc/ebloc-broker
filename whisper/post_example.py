#!/usr/bin/env python

import asyncio
import os.path
import sys
import time

from web3 import HTTPProvider, Web3

from config import env
from libs.whisper import log_loop
from utils import _colorize_traceback, log, read_json

w3 = Web3(HTTPProvider("http://localhost:8545"))

# Obtained from the node_1 and assigned here
receiver_pub = "0x049714e8e7b1a778e8631f76b1e0ab5ae9d0d7663020050d584b2512c4a67a2011b0c11412373f9ca88274957903863be1b01a6c6fecfc50051d64e7a1aa50b170"


def receiver(filter_id, public_key):
    retreived_messages = w3.geth.shh.getMessages(filter_id)
    log(f"==> whisper_id(public key):\n{public_key}", "blue")
    if len(retreived_messages) > 0:
        log("Received Messages:\n")
        for message in retreived_messages:
            log("==>" + message["payload"].decode("utf-8"))
            log("---------------------------------")

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(
            asyncio.gather(log_loop(filter_id, 2, is_return=True, public_key=public_key, is_reply_sinfo=False))
        )
    finally:
        loop.close()


if __name__ == "__main__":
    public_key = ""
    key_id = ""
    if not os.path.isfile(env.WHISPER_INFO):
        log("Please first run:")
        log(f"{env.EBLOCPATH}/whisper/initialize.py", "green")
        sys.exit(1)
    else:
        try:
            data = read_json(env.WHISPER_INFO)
        except:
            _colorize_traceback()
            sys.exit(1)

        key_id = data["key_id"]
        public_key = data["public_key"]
        if not w3.geth.shh.hasKeyPair(key_id):
            log("Whisper node's private key of a key pair did not match with the given ID")
            sys.exit(1)

        filter_id = data["filter_id"]

        log(f"filter_id={filter_id}")
        log(f"my_pub_key={public_key}")

    msg_filter = w3.geth.shh.new_message_filter(
        {"topic": env.WHISPER_TOPIC, "privateKeyID": key_id, "recipientPublicKey": public_key}
    )

    w3.geth.shh.post(
        {
            "powTarget": 2.5,
            "powTime": 2,
            "ttl": 60,
            "payload": public_key,
            "topic": env.WHISPER_TOPIC,
            "pubKey": receiver_pub,
        }
    )

    # ----
    receiver(filter_id, public_key)
    # time.sleep(4)
    # print(w3.geth.shh.get_filter_messages(msg_filter))
