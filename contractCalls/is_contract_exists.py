#!/usr/bin/env python3

import traceback

from imports import connect_to_web3
from settings import init_env
from utils import read_json

env = init_env()


def is_contract_exists():
    try:
        contract = read_json(f"{env.EBLOCPATH}/contractCalls/contract.json")
    except:
        print(traceback.format_exc())
        return False

    contract_address = contract["address"]

    w3 = connect_to_web3()
    contract_address = w3.toChecksumAddress(contract_address)
    if w3.eth.getCode(contract_address) == "0x" or w3.eth.getCode(contract_address) == b"":
        return False

    return True


if __name__ == "__main__":
    print(f"is_contract_exists={is_contract_exists()}")
