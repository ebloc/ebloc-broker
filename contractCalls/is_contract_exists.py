#!/usr/bin/env python3

import json
from os.path import expanduser

from imports import connect_to_web3


def is_contract_exists():
    home = expanduser("~")
    contract = json.loads(open(home + "/eBlocBroker/contractCalls/contract.json").read())
    contract_address = contract["address"]

    w3 = connect_to_web3()
    contract_address = w3.toChecksumAddress(contract_address)
    if w3.eth.getCode(contract_address) == "0x" or w3.eth.getCode(contract_address) == b"":
        return False

    return True


if __name__ == "__main__":
    print("is_contract_exists=" + str(is_contract_exists()))
