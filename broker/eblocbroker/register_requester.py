#!/usr/bin/env python3

import sys

import ipfshttpclient

import broker.cfg as cfg
from broker._utils.tools import QuietExit, log, print_tb
from broker.config import env
from broker.lib import get_tx_status, run

Ebb = cfg.Ebb


def register_requester(self, account_id, email, federation_cloud_id, gpg_fingerprint, ipfs_id):
    """Register or update requester into smart contract."""
    if env.IS_BLOXBERG:
        account = self.brownie_load_account().address
    else:
        account = self.w3.eth.accounts[int(account_id)]  # requester's Ethereum Address

    log(f"==> registering {account} as requester")
    if self.does_requester_exist(account):
        log(f"warning: Requester {account} is already registered")
        requester_info = Ebb.get_requester_info(account)
        if (
            requester_info["email"] == email
            and requester_info["gpg_fingerprint"] == gpg_fingerprint.lower()
            and requester_info["ipfs_id"] == ipfs_id
        ):
            log("Same requester information if provided, nothing to do")
            raise QuietExit

    if len(federation_cloud_id) >= 128:
        raise Exception("E: federation_cloud_id is more than 128")

    if len(email) >= 128:
        raise Exception("E: email is more than 128")

    if len(gpg_fingerprint) != 40:
        raise Exception("E: gpg_fingerprint should be 40 characters")

    try:
        tx = self._register_requester(account, gpg_fingerprint, email, federation_cloud_id, ipfs_id)
        return self.tx_id(tx)
    except Exception as e:
        print_tb(e)
        raise e


if __name__ == "__main__":
    try:
        client = ipfshttpclient.connect("/ip4/127.0.0.1/tcp/5001/http")
    except Exception as e:
        log("E: Run IPFS daemon to detect your ipfs_id")
        print_tb(e)
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
        gpg_fingerprint = run([env.BASH_SCRIPTS_PATH / "get_gpg_fingerprint.sh"])
        # gpg_fingerprint = "0x2AF4FEB13EA98C83D94150B675D5530929E05CEB"
        ipfs_id = cfg.ipfs.get_ipfs_id(client)

    try:
        tx_hash = Ebb.register_requester(account, email, federation_cloud_id, gpg_fingerprint, ipfs_id)
        receipt = get_tx_status(tx_hash)
    except QuietExit:
        pass
    except Exception as e:
        print_tb(e)
