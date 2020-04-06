#!/usr/bin/env python3

from imports import connect_to_web3
from utils import read_json

from settings import init_env

env = init_env()


def is_contract_exists():
    success, contract = read_json(f"{env.EBLOCPATH}/contractCalls/contract.json")
    if not success:
        return False

    contract_address = contract["address"]

    w3 = connect_to_web3()
    contract_address = w3.toChecksumAddress(contract_address)
    if w3.eth.getCode(contract_address) == "0x" or w3.eth.getCode(contract_address) == b"":
        return False

    return True


if __name__ == "__main__":
    print(f"is_contract_exists={is_contract_exists()}")
