#!/usr/bin/env python3

import sys

import ipfshttpclient

from lib import get_tx_status
from libs.whisper import check_whisper
from utils import _colorize_traceback, log


def register_requester(self, account_id, email, federation_cloud_id, gpg_fingerprint, ipfs_address):
    whisper_pub_key = check_whisper()
    account = self.w3.eth.accounts[int(account_id)]  # requester's Ethereum Address
    if not self.does_requester_exist(account):
        return f"Requester {account} is already registered."

    if len(federation_cloud_id) >= 128 and len(email) >= 128:
        return "E: federation_cloud_id or email is more than 128"

    try:
        tx = self.eBlocBroker.functions.registerRequester(
            gpg_fingerprint, email, federation_cloud_id, ipfs_address, "", whisper_pub_key,
        ).transact({"from": account, "gas": 4500000})
        return tx.hex()
    except Exception:
        _colorize_traceback()
        raise


if __name__ == "__main__":
    from _tools import bp
    import eblocbroker.Contract as Contract

    Ebb = Contract.eblocbroker
    try:
        alper = 100
        client = ipfshttpclient.connect("/ip4/127.0.0.1/tcp/5001/http")
    except:
        log("E: Run IPFS daemon", "red")
        exit(1)

    if len(sys.argv) == 6:
        account = int(sys.argv[1])
        email = str(sys.argv[2])
        federation_cloud_id = str(sys.argv[3])
        gpg_fingerprint = str(sys.argv[4])
        ipfs_address = str(sys.argv[5])
    else:
        account = 1  # requster's Ethereum Address
        email = "alper01234alper@gmail.com"  # "alper.alimoglu@gmail.com"
        federation_cloud_id = "059ab6ba-4030-48bb-b81b-12115f531296"
        gpg_fingerprint = "0x0359190A05DF2B72729344221D522F92EFA2F330"
        ipfs_address = client.id()["Addresses"][-1]

    try:
        tx_hash = Ebb.register_requester(account, email, federation_cloud_id, gpg_fingerprint, ipfs_address)
        receipt = get_tx_status(tx_hash)
    except:
        _colorize_traceback()
        sys.exit(1)
