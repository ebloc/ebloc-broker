#!/usr/bin/env python3


import os
import sys

from config import logging
from imports import connect, connect_to_web3
from lib import get_tx_status
from settings import init_env
from utils import _colorize_traceback, read_json

env = init_env()


def updateProviderInfo(email, federationCloudId, minilock_id, ipfsAddress):
    eBlocBroker, w3 = connect()

    if not os.path.isfile(f"{env.HOME}/.eBlocBroker/whisperInfo.txt"):
        logging.error("Please first run: ../scripts/whisper_initialize.py")
        raise
    else:
        try:
            data = read_json(f"{env.HOME}/.eBlocBroker/whisperInfo.txt")
        except:
            logging.error(_colorize_traceback())
            raise

        kId = data["kId"]
        whisperPubKey = data["publicKey"]
        if not w3.geth.shh.hasKeyPair(kId):
            logging.error(
                "Whisper node's private key of a key pair did not match with the given ID.\nPlease re-run: ../scripts/whisper_initialize.py"
            )
            raise

    if len(federationCloudId) < 128 and len(email) < 128 and (len(minilock_id) == 0 or len(minilock_id) == 45):
        try:
            tx = eBlocBroker.functions.updateProviderInfo(
                email, federationCloudId, minilock_id, ipfsAddress, whisperPubKey
            ).transact({"from": env.PROVIDER_ID, "gas": 4500000})
            return tx.hex()
        except Exception:
            logging.error(_colorize_traceback())
            raise


if __name__ == "__main__":
    email = "alper01234alper@gmail.com"
    federationCloudId = "5f0db7e4-3078-4988-8fa5-f066984a8a97@b2drop.eudat.eu"
    minilock_id = "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ"
    ipfsAddress = "/ip4/193.140.196.159/tcp/4001/ipfs/QmNQ74xaWquZseMhZJCPfV47WttP9hAoPEXeCMKsh3Cap4"

    try:
        w3 = connect_to_web3()
        tx_hash = updateProviderInfo(email, federationCloudId, minilock_id, ipfsAddress)
        receipt = get_tx_status(tx_hash)
    except:
        logging.error(_colorize_traceback())
        sys.exit(1)
