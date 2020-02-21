#!/usr/bin/env python3

import json
import os
import traceback
from os.path import expanduser

from dotenv import load_dotenv

from contractCalls.doesProviderExist import doesProviderExist
from imports import connect
from lib import EBLOCPATH, get_tx_status

home = expanduser("~")
load_dotenv(os.path.join(f"{home}/.eBlocBroker/", ".env"))  # Load .env from the given path

eBlocBroker, w3 = connect()
PROVIDER_ID = w3.toChecksumAddress(os.getenv("PROVIDER_ID"))


def register_provider(availableCoreNum, email, federationCloudId, miniLockId, prices, ipfsAddress, commitmentBlockNum):
    if not os.path.isfile(f"{home}/.eBlocBroker/whisperInfo.txt"):
        return False, "Please first run: ../scripts/whisperInitialize.py"
    else:
        with open(f"{home}/.eBlocBroker/whisperInfo.txt") as json_file:
            data = json.load(json_file)
            kId = data["kId"]
            whisperPubKey = data["publicKey"]

        if not w3.geth.shh.hasKeyPair(kId):
            return (
                False,
                f"Whisper node's private key of a key pair did not match with the given ID.\n"
                f"Please run: {EBLOCPATH}/scripts/whisperInitialize.py",
            )

    if doesProviderExist(PROVIDER_ID):
        return (
            False,
            f"Provider {PROVIDER_ID} is already registered. Please call the updateProvider() function for an update.",
        )

    if commitmentBlockNum < 240:
        return False, "Commitment block number should be greater than 240"

    if len(federationCloudId) < 128 and len(email) < 128 and (len(miniLockId) == 0 or len(miniLockId) == 45):
        try:
            tx = eBlocBroker.functions.registerProvider(
                email,
                federationCloudId,
                miniLockId,
                availableCoreNum,
                prices,
                commitmentBlockNum,
                ipfsAddress,
                whisperPubKey,
            ).transact({"from": PROVIDER_ID, "gas": 4500000})
        except Exception:
            return False, traceback.format_exc()

        return True, tx.hex()


if __name__ == "__main__":
    availableCoreNum = 128
    email = "alper01234alper@gmail.com"
    federationCloudId = "5f0db7e4-3078-4988-8fa5-f066984a8a97@b2drop.eudat.eu"
    miniLockId = "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ"
    ipfsAddress = "/ip4/79.123.177.145/tcp/4001/ipfs/QmWmZQnb8xh3gHf9ZFmVQC4mLEav3Uht5kHJxZtixG3rsf"

    priceCoreMin = 100
    priceDataTransfer = 1
    priceStorage = 1
    priceCache = 1
    prices = [priceCoreMin, priceDataTransfer, priceStorage, priceCache]

    commitmentBlockNum = 240

    status, result = register_provider(
        availableCoreNum, email, federationCloudId, miniLockId, prices, ipfsAddress, commitmentBlockNum
    )
    if status:
        receipt = get_tx_status(status, result)
    else:
        print(f"E: {result}")