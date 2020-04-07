#!/usr/bin/env python3

import os
import traceback

from contractCalls.doesProviderExist import doesProviderExist
from imports import connect
from lib import get_tx_status
from settings import init_env
from utils import read_json

eBlocBroker, w3 = connect()
env = init_env()


def register_provider(
    availableCoreNum, email, federation_cloud_id, minilock_id, prices, ipfsAddress, commitment_block_num,
):
    if not os.path.isfile(f"{env.HOME}/.eBlocBroker/whisperInfo.txt"):
        return False, "Please first run: ../scripts/whisper_initialize.py"
    else:
        success, data = read_json(f"{env.HOME}/.eBlocBroker/whisperInfo.txt")
        kId = data["kId"]
        whisperPubKey = data["publicKey"]

        if not w3.geth.shh.hasKeyPair(kId):
            return (
                False,
                f"Whisper node's private key of a key pair did not match with the given ID.\n"
                f"Please run: {env.EBLOCPATH}/scripts/whisper_initialize.py",
            )

    if doesProviderExist(env.PROVIDER_ID):
        return (
            False,
            f"Provider {env.PROVIDER_ID} is already registered. Please call the updateProvider() function for an update.",
        )

    if commitment_block_num < 240:
        return False, "Commitment block number should be greater than 240"

    if len(federation_cloud_id) < 128 and len(email) < 128 and (len(minilock_id) == 0 or len(minilock_id) == 45):
        try:
            tx = eBlocBroker.functions.registerProvider(
                email,
                federation_cloud_id,
                minilock_id,
                availableCoreNum,
                prices,
                commitment_block_num,
                ipfsAddress,
                whisperPubKey,
            ).transact({"from": env.PROVIDER_ID, "gas": 4500000})
        except Exception:
            return False, traceback.format_exc()

        return True, tx.hex()


if __name__ == "__main__":
    availableCoreNum = 128
    email = "alper01234alper@gmail.com"
    federation_cloud_id = "5f0db7e4-3078-4988-8fa5-f066984a8a97@b2drop.eudat.eu"
    minilock_id = "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ"
    ipfsAddress = "/ip4/79.123.177.145/tcp/4001/ipfs/QmWmZQnb8xh3gHf9ZFmVQC4mLEav3Uht5kHJxZtixG3rsf"

    priceCoreMin = 100
    priceDataTransfer = 1
    priceStorage = 1
    priceCache = 1
    prices = [priceCoreMin, priceDataTransfer, priceStorage, priceCache]

    commitment_block_num = 240

    success, output = register_provider(
        availableCoreNum, email, federation_cloud_id, minilock_id, prices, ipfsAddress, commitment_block_num,
    )
    if success:
        receipt = get_tx_status(success, output)
    else:
        print(f"E: {output}")
