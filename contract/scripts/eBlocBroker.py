#!/usr/bin/python3

import json

from brownie import Lib, accounts, eBlocBroker, network  # noqa


def main():
    # acct = accounts[0]
    acct = accounts.load("alper.json", password="alper")
    acct.deploy(Lib)
    ebb = acct.deploy(eBlocBroker)
    if network.show_active() == "private":
        from os.path import expanduser

        home = expanduser("~")
        BASE = f"{home}/ebloc-broker/broker/eblocbroker_scripts"
        abi_file = f"{BASE}/abi.json"
        contract_file = f"{BASE}/contract_bloxberg.json"
        json.dump(ebb.abi, open(abi_file, "w"))
        info = {"txHash": ebb.tx.txid, "address": ebb.address}
        with open(contract_file, "w") as fp:
            json.dump(info, fp)
