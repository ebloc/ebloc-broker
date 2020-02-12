#!/usr/bin/env python3

import json
from os.path import expanduser


def is_contract_exists(w3=None):
    home = expanduser("~")
    contract = json.loads(open(home + "/eBlocBroker/contractCalls/contract.json").read())
    contractAddress = contract["address"]

    if w3 is None:
        from imports import connect_to_web3

        w3 = connect_to_web3()

    contractAddress = w3.toChecksumAddress(contractAddress)
    if w3.eth.getCode(contractAddress) == "0x" or w3.eth.getCode(contractAddress) == b"":
        return False

    return True


if __name__ == "__main__":
    print("is_contract_exists=" + str(is_contract_exists()))
