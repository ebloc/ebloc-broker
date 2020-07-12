#!/usr/bin/python3

import json

from brownie import Lib, accounts, eBlocBroker, network


def main():
    accounts[0].deploy(Lib)
    ebb = accounts[0].deploy(eBlocBroker)

    if network.show_active() == "private":
        from os.path import expanduser
        home = expanduser("~")
        abi_file = f"{home}/eBlocBroker/eblocbroker/abi.json"
        contract_file = f"{home}/eBlocBroker/eblocbroker/contract.json"

        _file = open(abi_file,"w")
        json.dump(ebb.abi, _file)

        info = {'txHash': ebb.tx.txid, 'address': ebb.address}
        with open(contract_file, 'w') as fp:
            json.dump(info, fp)
