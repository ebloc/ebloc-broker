#!/usr/bin/env python

import asyncio
import os.path
import sys
import time

from web3 import HTTPProvider, Web3
from web3.auto import w3

from config import env
from lib import log
from utils import _colorize_traceback, read_json


def handle_event(event):
    print(event["payload"].decode("utf-8"))


async def log_loop(filter_id, poll_interval):
    while True:
        for event in w3.geth.shh.getMessages(filter_id):  # event_filter.get_new_entries():
            handle_event(event)  # TODO: add try catch
        await asyncio.sleep(poll_interval)
        time.sleep(0.25)


if __name__ == "__main__":
    web3 = Web3(HTTPProvider("http://localhost:8545"))
    print(web3.geth.shh.info)

    if not os.path.isfile(env.WHISPER_INFO):
        # first time running
        log("Please first run:")
        log("./whisper_initialize.py", "green")
        sys.exit(1)
    else:
        try:
            data = read_json(env.WHISPER_INFO)
        except:
            _colorize_traceback()

        key_id = data["key_id"]
        public_key = data["public_key"]
        if not w3.geth.shh.hasKeyPair(key_id):
            log("E: Whisper node's private key of a key pair did not match with the given ID", "red")
            sys.exit(1)

        filter_id = data["filter_id"]
        print(f"filter_id={filter_id}")

    retreived_messages = web3.geth.shh.getMessages(filter_id)
    print(f"topic={env.WHISPER_TOPIC}")
    log(f"public_key={public_key}", "green")

    """
    print('FilterID: ' + filter_id)
    print('receiverPrivateK: ' + web3.geth.shh.getPrivateKey(key_id));
    print(web3.geth.shh.hasKeyPair(key_id))
    print('PubKey: ' + web3.geth.shh.getPublicKey(key_id))
    """
    # retreived_messages = web3.geth.shh.getMessages('13723641127bc212ab379100a5d9e05e09b8c34fe1357f51e54cf17b568918cc')
    for message in retreived_messages:
        print(message["payload"].decode("utf-8"))
        print("---------------------------------")
        # print(retreived_messages[i])

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(asyncio.gather(log_loop(filter_id, 2)))
    finally:
        loop.close()
