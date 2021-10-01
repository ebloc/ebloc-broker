#!/usr/bin/env python3

import sys

import ipfshttpclient

import broker.cfg as cfg
from broker._utils.tools import QuietExit, log, print_tb
from broker.config import env
from broker.lib import get_tx_status


def register_provider(self, *args, **kwargs):
    """Register provider."""
    if self.does_provider_exist(env.PROVIDER_ID):
        log(
            f"Warning: Provider {env.PROVIDER_ID} is already registered.\n"
            "Please call the updateProvider() function for an update."
        )
        raise QuietExit

    if kwargs["commitment_blk"] < 240:
        raise Exception("E: Commitment block number should be greater than 240")

    if len(kwargs["federation_cloud_id"]) >= 128:
        raise Exception("E: federation_cloud_id hould be lesser than 128")

    if len(kwargs["email"]) >= 128:
        raise Exception("E: e-mail should be less than 128")

    try:
        tx = self.set_register_provider(*args)
        return self.tx_id(tx)
    except Exception as e:
        print_tb(e)
        raise e


if __name__ == "__main__":
    import broker.eblocbroker.Contract as Contract

    Ebb: "Contract.Contract" = Contract.EBB()
    try:
        ipfs_addr = "/ip4/127.0.0.1/tcp/5001/http"
        client = ipfshttpclient.connect(ipfs_addr)
    except Exception as e:
        print_tb(e)
        log(
            "E: Connection error to IPFS, please run it on the background.\n"
            "Please run ~/ebloc-broker/broker/daemons/ipfs.py"
        )
        sys.exit(1)

    try:
        ipfs_id = cfg.ipfs.get_ipfs_id(client, is_print=True)
    except Exception as e:
        print_tb(e)
        sys.exit(1)

    available_core = 128
    # email = "alper01234alper@gmail.com"
    email = "alper.alimoglu.research@gmail.com"
    federation_cloud_id = "5f0db7e4-3078-4988-8fa5-f066984a8a97@b2drop.eudat.eu"
    gpg_fingerprint = "0x11FBA2D03D3CFED18FC71D033B127BC747AADC1C"
    commitment_blk = 240
    price_core_min = 100
    price_data_transfer = 1
    price_storage = 1
    price_cache = 1
    prices = [price_core_min, price_data_transfer, price_storage, price_cache]
    args = (gpg_fingerprint, email, federation_cloud_id, ipfs_id, available_core, prices, commitment_blk)
    kwargs = {
        "email": email,
        "federation_cloud_id": federation_cloud_id,
        "commitment_blk": commitment_blk,
    }
    try:
        tx_hash = Ebb.register_provider(*args, **kwargs)
        receipt = get_tx_status(tx_hash)
    except Exception as e:
        if type(e).__name__ != "QuietExit":
            print_tb(e)
