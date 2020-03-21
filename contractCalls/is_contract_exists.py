#!/usr/bin/env python3

from imports import connect_to_web3
from lib import EBLOCPATH
from utils import read_json


def is_contract_exists():
    success, contract = read_json(f"{EBLOCPATH}/contractCalls/contract.json")
    if not success:
        return False

    contract_address = contract["address"]

    w3 = connect_to_web3()
    contract_address = w3.toChecksumAddress(contract_address)
    if w3.eth.getCode(contract_address) == "0x" or w3.eth.getCode(contract_address) == b"":
        return False

    return True


if __name__ == "__main__":
    print("is_contract_exists=" + str(is_contract_exists()))
