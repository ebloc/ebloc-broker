#!/usr/bin/env python3

import sys

from config import env, logging
from lib import get_tx_status
from libs.whisper import check_whisper
from utils import _colorize_traceback


def update_provider_info(self, gpg_fingerprint, email, federation_cloud_id, ipfs_address, whisper_pub_key):
    whisper_pub_key = check_whisper()
    if len(federation_cloud_id) >= 128:
        logging.error("E: federation_cloud_id hould be lesser than 128")
        raise

    if len(email) >= 128:
        logging.error("E: email should be less than 128")
        raise

    # if (len(gpg_fingerprint) == 0 or len(gpg_fingerprint) == 42):
    try:
        tx = self.eBlocBroker.functions.updateProviderInfo(
            gpg_fingerprint, email, federation_cloud_id, ipfs_address, whisper_pub_key
        ).transact({"from": env.PROVIDER_ID, "gas": 4500000})
        return tx.hex()
    except Exception:
        _colorize_traceback()
        raise


if __name__ == "__main__":
    import eblocbroker.Contract as Contract

    Ebb = Contract.eblocbroker
    gpg_fingerprint = "0359190A05DF2B72729344221D522F92EFA2F330"
    email = "alper.alimoglu.research@gmail.com"
    federation_cloud_id = "5f0db7e4-3078-4988-8fa5-f066984a8a97@b2drop.eudat.eu"
    ipfs_address = ""
    whisper_pub_key = ""
    try:
        tx_hash = Ebb.update_provider_info(gpg_fingerprint, email, federation_cloud_id, ipfs_address, whisper_pub_key)
        receipt = get_tx_status(tx_hash)
    except:
        _colorize_traceback()
        sys.exit(1)
