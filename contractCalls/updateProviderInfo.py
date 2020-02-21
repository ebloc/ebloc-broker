#!/usr/bin/env python3

import json
import os
import traceback
from os.path import expanduser

from imports import connect, connect_to_web3
from lib import get_tx_status

home = expanduser("~")


def updateProviderInfo(email, federationCloudId, miniLockId, ipfsAddress):
    eBlocBroker, w3 = connect()
    if eBlocBroker is None or w3 is None:
        return

    PROVIDER_ID = w3.toChecksumAddress(os.getenv("PROVIDER_ID"))
    if not os.path.isfile(home + "/.eBlocBroker/whisperInfo.txt"):
        return False, "Please first run: ../scripts/whisperInitialize.py"
    else:
        with open(home + "/.eBlocBroker/whisperInfo.txt") as json_file:
            data = json.load(json_file)
            kId = data["kId"]
            whisperPubKey = data["publicKey"]
        if not w3.geth.shh.hasKeyPair(kId):
            return (
                False,
                "Whisper node's private key of a key pair did not match with the given ID.\nPlease re-run: ../scripts/whisperInitialize.py",
            )

    if len(federationCloudId) < 128 and len(email) < 128 and (len(miniLockId) == 0 or len(miniLockId) == 45):
        try:
            tx = eBlocBroker.functions.updateProviderInfo(
                email, federationCloudId, miniLockId, ipfsAddress, whisperPubKey
            ).transact({"from": PROVIDER_ID, "gas": 4500000})
        except Exception:
            return False, traceback.format_exc()

        return True, tx.hex()


if __name__ == "__main__":
    email = "alper01234alper@gmail.com"
    federationCloudId = "5f0db7e4-3078-4988-8fa5-f066984a8a97@b2drop.eudat.eu"
    miniLockId = "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ"
    ipfsAddress = "/ip4/193.140.196.159/tcp/4001/ipfs/QmNQ74xaWquZseMhZJCPfV47WttP9hAoPEXeCMKsh3Cap4"

    w3 = connect_to_web3()
    status, result = updateProviderInfo(email, federationCloudId, miniLockId, ipfsAddress)
    if status:
        receipt = get_tx_status(status, result)
    else:
        print(result)
