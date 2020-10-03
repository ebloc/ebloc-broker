#!/usr/bin/env python

import asyncio
import itertools
import json
import os
import sys

from web3 import HTTPProvider, Web3
from web3.shh import Shh

from utils import _colorize_traceback, read_json

web3 = Web3(HTTPProvider("http://localhost:8545"))

Shh.attach(web3, "shh")


def handle_event(event):
    # print(event)
    print(event["payload"].decode("utf-8"))
    return True


async def log_loop(event_filter, poll_interval):
    for idx in itertools.count(0):
        if idx == 5:
            break
        for event in event_filter.get_new_entries():
            if handle_event(event):
                return
        await asyncio.sleep(poll_interval)


if __name__ == "__main__":
    topic = "0x07678231"

    if not os.path.isfile("data.txt"):
        # first time running
        print("Initializing...")
        key_id = web3.shh.newKeyPair()
        public_key = web3.shh.getPublicKey(key_id)

        msg_filter = web3.shh.newMessageFilter({"topic": topic, "privateKeyID": key_id, "recipientPublicKey": public_key})
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
            data = read_json("data.txt")
        except:
            _colorize_traceback()
            sys.exit(1)

        key_id = data["key_id"]
        public_key = data["public_key"]

    print(public_key)

    msg_filter = web3.shh.newMessageFilter({"topic": topic, "privateKeyID": key_id, "recipientPublicKey": public_key})
    msg_filter.poll_interval = 600
    # make it equal with the live-time of the message
    filter_id = msg_filter.filter_id

    # Obtained from node_1 and assigned here.
    receiver_pub = "0x04b3b8efbea4fbdcbaee11771a23bb76ec571aee4c0a78e52b0705822146e70a59b8e92eade03393c78b3f6bf6890564abf0ecc664a382cf59c5a59075abc99d6a"

    payloads = [web3.toHex(text=public_key), web3.toHex(text="2nd test message")]

    web3.shh.post(
        {
            "powTarget": 2,  # 2.5
            "powTime": 5,  # 2
            "ttl": 60,
            "payload": payloads[0],
            "topic": topic,
            # 'targetPeer': "",
            "pubKey": receiver_pub,
        }
    )
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(asyncio.gather(log_loop(msg_filter, 2)))
    finally:
        loop.close()
