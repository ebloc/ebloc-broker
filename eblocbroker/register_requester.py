#!/usr/bin/env python3

import sys

from lib import get_tx_status
from libs.whisper import check_whisper
from utils import _colorize_traceback


def register_requester(self, account_id, email, federationCloudID, gpg_fingerprint, ipfsAddress, githubUsername):
    whisper_pub_key = check_whisper()
    account = self.w3.eth.accounts[int(account_id)]  # requester's Ethereum Address
    if not self.does_requester_exist(account):
        return f"Requester {account} is already registered."

    if len(federationCloudID) >= 128 and len(email) >= 128:
        return "E: federationCloudID or email is more than 128"

    try:
        tx = self.eBlocBroker.functions.registerRequester(
            gpg_fingerprint, email, federationCloudID, ipfsAddress, githubUsername, whisper_pub_key,
        ).transact({"from": account, "gas": 4500000})
        return tx.hex()
    except Exception:
        _colorize_traceback()
        raise


if __name__ == "__main__":
    import eblocbroker.Contract as Contract

    Ebb = Contract.eblocbroker

    if len(sys.argv) == 7:
        account = int(sys.argv[1])
        email = str(sys.argv[2])
        federationCloudID = str(sys.argv[3])
        gpg_fingerprint = str(sys.argv[4])
        ipfsAddress = str(sys.argv[5])
        githubUsername = str(sys.argv[6])
    else:
        account = 1  # requster's Ethereum Address
        email = "alper01234alper@gmail.com"  # "alper.alimoglu@gmail.com"
        federationCloudID = "059ab6ba-4030-48bb-b81b-12115f531296"
        gpg_fingerprint = "0x0359190A05DF2B72729344221D522F92EFA2F330"
        ipfsAddress = "/ip4/79.123.177.145/tcp/4001/ipfs/QmWmZQnb8xh3gHf9ZFmVQC4mLEav3Uht5kHJxZtixG3rsf"
        githubUsername = "eBloc"

    try:
        tx_hash = Ebb.register_requester(
            account, email, federationCloudID, gpg_fingerprint, ipfsAddress, githubUsername
        )
        receipt = get_tx_status(tx_hash)
    except:
        _colorize_traceback()
        sys.exit(1)
