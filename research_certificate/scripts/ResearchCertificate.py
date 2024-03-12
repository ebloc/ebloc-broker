#!/usr/bin/python3

import json

from brownie import ResearchCertificate, accounts, network


def main():
    acct = accounts.load("alper.json", password="alper")
    print(f"from={acct}")
    roc = ResearchCertificate.deploy({"from": acct})
    if network.show_active() == "private":
        from os.path import expanduser

        home = expanduser("~")
        BASE = f"{home}/ebloc-broker/broker/eblocbroker_scripts"
        abi_file = f"{BASE}/abi_ResearchCertificate.json"
        contract_file = f"{BASE}/contract_ResearchCertificate.json"
        json.dump(auto.abi, open(abi_file, "w"))
        info = {"txHash": auto.tx.txid, "address": auto.address}
        with open(contract_file, "w") as fp:
            json.dump(info, fp)
    elif network.show_active() == "development":
        print("development")
