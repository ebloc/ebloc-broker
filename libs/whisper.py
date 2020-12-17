#!/usr/bin/env python3

import asyncio
import os
import pprint
import sys
import time

from hexbytes import HexBytes
from web3 import HTTPProvider, Web3

from config import env
from lib import run_command
from utils import _colorize_traceback, log, read_json

pp = pprint.PrettyPrinter(indent=4)

w3 = Web3(HTTPProvider("http://localhost:8545"))
public_key = None


def check_whisper():
    if not os.path.isfile(env.WHISPER_INFO):
        log(f"Run: {env.EBLOCPATH}/whisper/initialize.py", "yellow")
        raise

    try:
        data = read_json(env.WHISPER_INFO)
        key_id = data["key_id"]
        whisper_pub_key = data["public_key"]
        if not w3.geth.shh.hasKeyPair(key_id):
            log("E: Whisper node's private key of a key pair did not match with the given ID", "red")
            raise
    except:
        log("Please first run:")
        log(f"{env.EBLOCPATH}/whisper/initialize.py", "green")
        _colorize_traceback()
        raise
    return whisper_pub_key


def reply_sinfo(recipient_public_key, my_public_key):
    # https://stackoverflow.com/a/50095154/2402577
    cmd = ["sinfo", "-h", "-o%C"]
    success, output = run_command(cmd)
    print(f"CPUS(A/I/O/T)={output}")
    output = output.split("/")
    allocated_core = output[1]
    idle_core = output[1]
    if success and my_public_key != recipient_public_key:
        try:
            w3.geth.shh.post(
                {
                    "powTarget": 2,  # 2.5
                    "powTime": 5,  # 2
                    "ttl": 60,
                    "payload": w3.toHex(text=f"online/{allocated_core}/{idle_core}"),
                    "topic": env.WHISPER_TOPIC,
                    "pubKey": recipient_public_key,
                }
            )
        except Exception as e:
            print(str(e))
            sys.exit(1)
            # reply_sinfo(recipient_public_key, my_public_key)
    else:
        log("E: Sender and receivers public keys are same", "blue")


def handle_event(event, public_key, is_reply_sinfo=False):
    # pp.pprint(event)
    if is_reply_sinfo:
        message = event["payload"].hex()  # received text is the sender's public-id
        reply_sinfo(message, public_key)
    else:
        log(event["payload"].decode("utf-8"), color="blue")
        return


async def log_loop(filter_id, poll_interval, is_return=False, public_key="", is_reply_sinfo=False):
    log(f"Listening started.\npublic_key={public_key}", "green")
    sleep_duration = 0
    while True:
        sys.stdout.write("\r==> Waiting Whisper messages for {:1d} seconds...".format(sleep_duration))
        sys.stdout.flush()
        for event in w3.geth.shh.getMessages(filter_id):
            try:
                handle_event(event, public_key, is_reply_sinfo)
                if is_return:
                    return True
            except:
                _colorize_traceback()

        sleep_duration += poll_interval
        await asyncio.sleep(poll_interval)
        time.sleep(0.25)
