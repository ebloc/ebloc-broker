#!/usr/bin/env python

import asyncio
import os.path
import sys
from os.path import expanduser

from web3 import HTTPProvider, Web3
from web3.auto import w3

from lib import log
from utils import _colorize_traceback, read_json

home = expanduser("~")


def handle_event(event):
    # print(event)
    print(event["payload"].decode("utf-8"))
    # and whatever


async def log_loop(filter_id, poll_interval):
    while True:
        for event in w3.geth.shh.getMessages(filter_id):  # event_filter.get_new_entries():
            handle_event(event)  # TODO: add try catch
        await asyncio.sleep(poll_interval)


if __name__ == "__main__":
    topic = "0x07678231"

    web3 = Web3(HTTPProvider("http://localhost:8545"))
    print(web3.geth.shh.info)

    if not os.path.isfile(home + "/.eBlocBroker/whisperInfo.txt"):
        # first time running
        log("Please first run: python whisper_initialize.py")
        sys.exit(1)
    else:
        try:
            data = read_json(home + "/.eBlocBroker/whisperInfo.txt")
        except:
            log(_colorize_traceback())

        kId = data["kId"]
        publicKey = data["publicKey"]
        if not w3.geth.shh.hasKeyPair(kId):
            log("Whisper node's private key of a key pair did not match with the given ID")
            sys.exit(1)

        filter_id = data["filter_id"]
        print("filter_id=" + filter_id)

    retreived_messages = web3.geth.shh.getMessages(filter_id)

    print("publicKeyK: " + publicKey)
    """
    print('FilterID: ' + filter_id)
    print('receiverPrivateK: ' + web3.geth.shh.getPrivateKey(kId));
    print(web3.geth.shh.hasKeyPair(kId))
    print('PubKey: ' + web3.geth.shh.getPublicKey(kId))
    """
    # retreived_messages = web3.geth.shh.getMessages('13723641127bc212ab379100a5d9e05e09b8c34fe1357f51e54cf17b568918cc')

    for i in range(0, len(retreived_messages)):
        print(retreived_messages[i]["payload"].decode("utf-8"))
        print("---------------------------------")
        # print(retreived_messages[i])

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(asyncio.gather(log_loop(filter_id, 2)))
    finally:
        loop.close()
