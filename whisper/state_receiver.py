#!/usr/bin/env python3

import asyncio
import os.path
import sys

from web3 import HTTPProvider, Web3

from config import env
from libs.whisper import log_loop
from utils import _colorize_traceback, log, read_json

w3 = Web3(HTTPProvider("http://localhost:8545"))

env.log_filename = env.WHISPER_LOG


def receiver(filter_id, public_key):
    retreived_messages = w3.geth.shh.getMessages(filter_id)
    log(f"whisper_id(public key)={public_key}", "blue")

    """
    log('FilterID: ' + filter_id)
    log('receiverPrivateK: ' + w3.geth.shh.getPrivateKey(key_id));
    log(w3.geth.shh.hasKeyPair(key_id))
    log('PubKey: ' + w3.geth.shh.getPublicKey(key_id))
    """
    # retreived_messages = w3.geth.shh.getMessages('13723641127bc212ab379100a5d9e05e09b8c34fe1357f51e54cf17b568918cc')
    if len(retreived_messages) > 0:
        log("Received Messages:\n")
        for message in retreived_messages:
            log(
                message["payload"].decode("utf-8"), "white",
            )
            log("---------------------------------")

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(
            asyncio.gather(log_loop(filter_id, 2, is_return=False, public_key=public_key, is_reply_sinfo=True))
        )
    finally:
        loop.close()


def main():
    if not os.path.isfile(env.WHISPER_INFO):
        log("Please first run:")
        log(f"{env.EBLOCPATH}/python_scripts/whisper_initialize.py", "green")
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
            log("\nWhisper node's private key of a key pair did not match with the given ID")
            sys.exit(1)

        # my_filter = w3.geth.shh.new_message_filter({'topic': env.WHISPER_TOPIC, 'privateKeyID': key_id, 'recipientPublicKey': public_key})
        # my_filter.poll_interval = 600; # make it equal with the live-time of the message
        filter_id = data["filter_id"]
        log(f"filter_id={filter_id}")
        # my_filter = w3.eth.filter(filter_id=filter_id)
        # privateKey = "0xc0995bb51a0a74fcedf972662569849de4b4d0e8ceca8e4e6e8846a5d00f0b0c"
        # key_id = w3.geth.shh.addPrivateKey(privateKey)

    receiver(filter_id, public_key)


if __name__ == "__main__":
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        main()
