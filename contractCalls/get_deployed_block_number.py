#!/usr/bin/env python3

import json
from os.path import expanduser

import config
from imports import connect_to_web3

home = expanduser("~")


def get_deployed_block_number():
    if config.w3 is None:
        config.w3 = connect_to_web3()

    if not config.w3:
        return False

    contract = json.loads(open(home + "/eBlocBroker/contractCalls/contract.json").read())
    return config.w3.eth.getTransaction(contract["txHash"]).blockNumber


if __name__ == "__main__":
    print(get_deployed_block_number())
