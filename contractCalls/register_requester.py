#!/usr/bin/env python3

import os
import sys
import traceback
from os.path import expanduser

from config import load_log
from does_requester_exist import does_requester_exist
from imports import connect, connect_to_web3
from lib import get_tx_status
from utils import read_json


def register_requester(account_id, email, federationCloudID, miniLockID, ipfsAddress, githubUsername):
    eBlocBroker, w3 = connect()
    if eBlocBroker is None or w3 is None:
        return

    home = expanduser("~")
    if not os.path.isfile(f"{home}/.eBlocBroker/whisperInfo.txt"):
        return (
            False,
            "Please first run: python ~/eBlocBroker/scripts/whisper_initialize.py",
        )
    else:
        try:
            data = read_json(f"{home}/.eBlocBroker/whisperInfo.txt")
        except:
            logging.error(traceback.format_exc())
            return False

        kId = data["kId"]
        whisperPubKey = data["publicKey"]
        if not w3.geth.shh.hasKeyPair(kId):
            return (
                False,
                "Whisper node's private key of a key pair did not match with the given ID",
            )

    account = w3.eth.accounts[int(account_id)]  # requester's Ethereum Address
    if does_requester_exist(account):
        return False, f"Requester {account} is already registered."

    if len(federationCloudID) < 128 and len(email) < 128:
        try:
            tx = eBlocBroker.functions.registerRequester(
                email, federationCloudID, miniLockID, ipfsAddress, githubUsername, whisperPubKey,
            ).transact({"from": account, "gas": 4500000})
        except Exception:
            return False, traceback.format_exc()

        return True, tx.hex()


if __name__ == "__main__":
    global logging
    logging = load_log()

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
    success, output = register_requester(account, email, federationCloudID, miniLockID, ipfsAddress, githubUsername)
    if success:
        receipt = get_tx_status(success, output)
    else:
        logging.error(f"E: {output}")
