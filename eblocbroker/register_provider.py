#!/usr/bin/env python3

import os
import sys

import ipfshttpclient

from config import env, logging
from lib import get_tx_status
from utils import _colorize_traceback, log, read_json


def register_provider(
    self, available_core, email, federation_cloud_id, gpg_fingerprint, prices, ipfs_id, commitment_block
):
    if not os.path.isfile(f"{env.HOME}/.eBlocBroker/whisper_info.json"):
        logging.error(f"Please first run:\n{env.HOME}/eBlocBroker/whisper/initialize.py")
        raise

    try:
        data = read_json(f"{env.HOME}/.eBlocBroker/whisper_info.json")
    except:
        _colorize_traceback()
        raise

    key_id = data["key_id"]
    whisper_pub_key = data["public_key"]

    if not self.w3.geth.shh.hasKeyPair(key_id):
        logging.error("\nWhisper node's private key of a key pair did not match with the given ID. Please run:")
        log(f"{env.EBLOCPATH}/whisper/initialize.py \n", "yellow")
        raise

    if self.does_provider_exist(env.PROVIDER_ID):
        log(
            "E: Provider {env.PROVIDER_ID} is already registered.\n"
            "Please call the updateProvider() function for an update.",
            c="red",
        )
        raise

    if commitment_block < 240:
        logging.error("E: Commitment block number should be greater than 240")
        raise

    if len(federation_cloud_id) >= 128:
        logging.error("E: federation_cloud_id hould be lesser than 128")
        raise

    if len(email) >= 128:
        logging.error("E: email should be less than 128")
        raise

    try:
        tx = self.eBlocBroker.functions.registerProvider(
            gpg_fingerprint,
            email,
            federation_cloud_id,
            ipfs_id,
            whisper_pub_key,
            available_core,
            prices,
            commitment_block,
        ).transact({"from": env.PROVIDER_ID, "gas": 4500000})
        return tx.hex()
    except Exception:
        logging.error(_colorize_traceback)
        raise


if __name__ == "__main__":
    import eblocbroker.Contract as Contract
    addr = "/ip4/127.0.0.1/tcp/5001/http"
    try:
        client = ipfshttpclient.connect(addr)
        print(client)
    except Exception:
        _colorize_traceback()
        log("E: Connection error to IPFS, please run it on the background.\nPlease run ~/eBlocBroker/daemons/ipfs.py", "red")
        sys.exit(1)

    Ebb = Contract.eblocbroker
    # https://github.com/ipfs-shipyard/py-ipfs-http-client
    client = ipfshttpclient.connect(addr)

    available_core = 128
    email = "alper01234alper@gmail.com"
    federation_cloud_id = "5f0db7e4-3078-4988-8fa5-f066984a8a97@b2drop.eudat.eu"
    gpg_fingerprint = "0x0359190A05DF2B72729344221D522F92EFA2F330"

    ipfs_id = client.id()["Addresses"][-1]
    print(f"ipfs_id={ipfs_id}\n")

    price_core_min = 100
    price_data_transfer = 1
    price_storage = 1
    price_cache = 1
    prices = [price_core_min, price_data_transfer, price_storage, price_cache]
    commitment_block = 240

    try:
        tx_hash = Ebb.register_provider(
            available_core, email, federation_cloud_id, gpg_fingerprint, prices, ipfs_id, commitment_block,
        )
        receipt = get_tx_status(tx_hash)
    except:
        _colorize_traceback()
