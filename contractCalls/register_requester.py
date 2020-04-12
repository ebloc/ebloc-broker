#!/usr/bin/env python3

import os
import sys
from os.path import expanduser

from config import logging
from does_requester_exist import does_requester_exist
from imports import connect, connect_to_web3
from lib import get_tx_status
from utils import _colorize_traceback, read_json


def register_requester(account_id, email, federationCloudID, miniLockID, ipfsAddress, githubUsername):
    eBlocBroker, w3 = connect()
    if eBlocBroker is None or w3 is None:
        return

    home = expanduser("~")
    if not os.path.isfile(f"{home}/.eBlocBroker/whisperInfo.txt"):
        logging.error("Please first run: python ~/eBlocBroker/scripts/whisper_initialize.py")
        raise
    else:
        try:
            data = read_json(f"{home}/.eBlocBroker/whisperInfo.txt")
        except:
            logging.error(_colorize_traceback())
            raise

        kId = data["kId"]
        whisperPubKey = data["publicKey"]
        if not w3.geth.shh.hasKeyPair(kId):
            logging.error("Whisper node's private key of a key pair did not match with the given ID",)
            raise

    account = w3.eth.accounts[int(account_id)]  # requester's Ethereum Address
    if does_requester_exist(account):
        return False, f"Requester {account} is already registered."

    if len(federationCloudID) < 128 and len(email) < 128:
        try:
            tx = eBlocBroker.functions.registerRequester(
                email, federationCloudID, miniLockID, ipfsAddress, githubUsername, whisperPubKey,
            ).transact({"from": account, "gas": 4500000})
            return tx.hex()
        except Exception:
            logging.error(_colorize_traceback())
            raise


if __name__ == "__main__":
    if len(sys.argv) == 7:
        account = int(sys.argv[1])
        email = str(sys.argv[2])
        federationCloudID = str(sys.argv[3])
        miniLockID = str(sys.argv[4])
        ipfsAddress = str(sys.argv[5])
        githubUsername = str(sys.argv[6])
    else:
        account = 1  # requster's Ethereum Address
        email = "alper01234alper@gmail.com"  # "alper.alimoglu@gmail.com"
        federationCloudID = "059ab6ba-4030-48bb-b81b-12115f531296"
        miniLockID = "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ"
        ipfsAddress = "/ip4/79.123.177.145/tcp/4001/ipfs/QmWmZQnb8xh3gHf9ZFmVQC4mLEav3Uht5kHJxZtixG3rsf"
        githubUsername = "eBloc"

    w3 = connect_to_web3()

    try:
        tx_hash = register_requester(account, email, federationCloudID, miniLockID, ipfsAddress, githubUsername)
        receipt = get_tx_status(tx_hash)
    except:
        logging.error(_colorize_traceback())
        sys.exit(1)
