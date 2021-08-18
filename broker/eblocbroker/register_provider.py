#!/usr/bin/env python3

import sys

import ipfshttpclient

from broker._utils.tools import _colorize_traceback, log
from broker.config import QuietExit, env
from broker.lib import get_tx_status
from broker.libs.ipfs import get_ipfs_id


def register_provider(
    self, available_core, email, federation_cloud_id, gpg_fingerprint, prices, ipfs_id, commitment_block
):
    """Register provider."""
    if self.does_provider_exist(env.PROVIDER_ID):
        log(
            f"E: Provider {env.PROVIDER_ID} is already registered.\n"
            "Please call the updateProvider() function for an update."
        )
        raise QuietExit

    if commitment_block < 240:
        log("E: Commitment block number should be greater than 240")
        raise

    if len(federation_cloud_id) >= 128:
        log("E: federation_cloud_id hould be lesser than 128")
        raise

    if len(email) >= 128:
        log("E: e-mail should be less than 128")
        raise

    try:
        tx = self.set_register_provider(
            gpg_fingerprint, email, federation_cloud_id, ipfs_id, available_core, prices, commitment_block
        )
        return self.tx_id(tx)
    except Exception as e:
        _colorize_traceback(e)
        raise e


if __name__ == "__main__":
    import broker.eblocbroker.Contract as Contract

    Ebb = Contract.eblocbroker = Contract.Contract()
    try:
        ipfs_addr = "/ip4/127.0.0.1/tcp/5001/http"
        client = ipfshttpclient.connect(ipfs_addr)
    except Exception as e:
        _colorize_traceback(e)
        log(
            "E: Connection error to IPFS, please run it on the background.\n"
            "Please run ~/ebloc-broker/broker/daemons/ipfs.py"
        )
        sys.exit(1)

    try:
        ipfs_id = get_ipfs_id(client, is_print=True)
    except Exception as e:
        _colorize_traceback(e)
        sys.exit(1)

    available_core = 128
    # email = "alper01234alper@gmail.com"
    email = "alper.alimoglu.research@gmail.com"
    federation_cloud_id = "5f0db7e4-3078-4988-8fa5-f066984a8a97@b2drop.eudat.eu"
    gpg_fingerprint = "0x11FBA2D03D3CFED18FC71D033B127BC747AADC1C"

    price_core_min = 100
    price_data_transfer = 1
    price_storage = 1
    price_cache = 1

    prices = [price_core_min, price_data_transfer, price_storage, price_cache]
    commitment_block = 240
    try:
        tx_hash = Ebb.register_provider(
            available_core,
            email,
            federation_cloud_id,
            gpg_fingerprint,
            prices,
            ipfs_id,
            commitment_block,
        )
        receipt = get_tx_status(tx_hash)
    except Exception as e:
        if type(e).__name__ != "QuietExit":
            _colorize_traceback(e)