#!/usr/bin/env python3

import sys

import ipfshttpclient

import broker.cfg as cfg
from broker._utils.tools import QuietExit, _colorize_traceback, log
from broker.config import env
from broker.lib import get_tx_status


def register_requester(self, account_id, email, federation_cloud_id, gpg_fingerprint, ipfs_id):
    """Register requester into smart contract."""
    if env.IS_BLOXBERG:
        account = self.brownie_load_accounts().address
    else:
        account = self.w3.eth.accounts[int(account_id)]  # requester's Ethereum Address

    log(f"==> registering {account} as requester")
    if self.does_requester_exist(account):
        log(f"E: Requester {account} is already registered.")
        raise QuietExit

    if len(federation_cloud_id) >= 128:
        raise Exception("E: federation_cloud_id is more than 128")

    if len(email) >= 128:
        raise Exception("E: email is more than 128")

    try:
        tx = self._register_requester(account, gpg_fingerprint, email, federation_cloud_id, ipfs_id)
        return self.tx_id(tx)
    except Exception as e:
        _colorize_traceback(e)
        raise e


if __name__ == "__main__":
    import broker.eblocbroker.Contract as Contract

    Ebb = Contract.ebb()
    try:
        client = ipfshttpclient.connect("/ip4/127.0.0.1/tcp/5001/http")
    except:
        log("E: Run IPFS daemon to detect your ipfs_id")
        sys.exit(1)

    if len(sys.argv) == 6:
        account = int(sys.argv[1])
        email = str(sys.argv[2])
        federation_cloud_id = str(sys.argv[3])
        gpg_fingerprint = str(sys.argv[4])
        ipfs_id = str(sys.argv[5])
    else:
        account = 1  # requster's Ethereum Address
        email = "alper01234alper@gmail.com"  # "alper.alimoglu@gmail.com"
        federation_cloud_id = "059ab6ba-4030-48bb-b81b-12115f531296"
        gpg_fingerprint = "0x1B626A5D0C49D7376F73EEB0A1106434B2696907"  # info: get_gpg_fingerprint.sh
        ipfs_id = cfg.ipfs.get_ipfs_id(client, is_print=True)

    try:
        tx_hash = Ebb.register_requester(account, email, federation_cloud_id, gpg_fingerprint, ipfs_id)
        receipt = get_tx_status(tx_hash)
    except Exception as e:
        if type(e).__name__ != "QuietExit":
            _colorize_traceback()
        sys.exit(1)
