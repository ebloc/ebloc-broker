#!/usr/bin/env python3

import os

from config import logging
from contractCalls.doesProviderExist import doesProviderExist
from imports import connect
from lib import get_tx_status
from settings import init_env
from utils import _colorize_traceback, read_json

env = init_env()


def register_provider(
    availableCoreNum, email, federation_cloud_id, minilock_id, prices, ipfsAddress, commitment_block_num,
):
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
                f"Whisper node's private key of a key pair did not match with the given ID.\n"
                f"Please run: {env.EBLOCPATH}/scripts/whisper_initialize.py"
            )
            raise

    if doesProviderExist(env.PROVIDER_ID):
        logging.error(
            f"Provider {env.PROVIDER_ID} is already registered. Please call the updateProvider() function for an update."
        )
        raise

    if commitment_block_num < 240:
        logging.error("Commitment block number should be greater than 240")
        raise

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
            return tx.hex()
        except Exception:
            logging.error(_colorize_traceback)
            raise


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

    try:
        tx_hash = register_provider(
            availableCoreNum, email, federation_cloud_id, minilock_id, prices, ipfsAddress, commitment_block_num,
        )
        receipt = get_tx_status(tx_hash)
    except:
        print(_colorize_traceback())
