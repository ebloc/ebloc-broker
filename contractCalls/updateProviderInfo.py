#!/usr/bin/env python3


import os
import traceback

from imports import connect, connect_to_web3
from lib import get_tx_status
from utils import read_json

from settings import init_env

env = init_env()


def updateProviderInfo(email, federationCloudId, minilock_id, ipfsAddress):
    eBlocBroker, w3 = connect()
    if eBlocBroker is None or w3 is None:
        return

    if not os.path.isfile(f"{env.HOME}/.eBlocBroker/whisperInfo.txt"):
        return False, "Please first run: ../scripts/whisper_initialize.py"
    else:
        success, data = read_json(f"{env.HOME}/.eBlocBroker/whisperInfo.txt")
        kId = data["kId"]
        whisperPubKey = data["publicKey"]
        if not w3.geth.shh.hasKeyPair(kId):
            return (
                False,
                "Whisper node's private key of a key pair did not match with the given ID.\nPlease re-run: ../scripts/whisper_initialize.py",
            )

    if len(federationCloudId) < 128 and len(email) < 128 and (len(minilock_id) == 0 or len(minilock_id) == 45):
        try:
            tx = eBlocBroker.functions.updateProviderInfo(
                email, federationCloudId, minilock_id, ipfsAddress, whisperPubKey
            ).transact({"from": env.PROVIDER_ID, "gas": 4500000})
        except Exception:
            return False, traceback.format_exc()

        return True, tx.hex()


if __name__ == "__main__":
    email = "alper01234alper@gmail.com"
    federationCloudId = "5f0db7e4-3078-4988-8fa5-f066984a8a97@b2drop.eudat.eu"
    minilock_id = "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ"
    ipfsAddress = "/ip4/193.140.196.159/tcp/4001/ipfs/QmNQ74xaWquZseMhZJCPfV47WttP9hAoPEXeCMKsh3Cap4"

    w3 = connect_to_web3()
    success, output = updateProviderInfo(email, federationCloudId, minilock_id, ipfsAddress)
    if success:
        receipt = get_tx_status(success, output)
    else:
        print(output)
