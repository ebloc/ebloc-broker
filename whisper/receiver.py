#!/usr/bin/env python

import asyncio
import json
import os.path
import sys
from os.path import expanduser

from web3 import HTTPProvider, Web3
from web3.auto import w3

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


def main():
    topic = "0x07678231"

    web3 = Web3(HTTPProvider("http://localhost:8545"))
    print(web3.geth.shh.info)

    if not os.path.isfile(home + "/.eBlocBroker/whisperInfo.txt"):
        # First time running:
        log("Please first run: python whisperInitialize.py")
        sys.exit()
    else:
        with open(home + "/.eBlocBroker/whisperInfo.txt") as json_file:
            data = json.load(json_file)

        kId = data["kId"]
        publicKey = data["publicKey"]
        if not w3.geth.shh.hasKeyPair(kId):
            log("Whisper node's private key of a key pair did not match with the given ID")
            sys.exit()

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


if __name__ == "__main__":
    main()
