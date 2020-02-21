#!/usr/bin/env python3

import json
from os.path import expanduser

from web3 import IPCProvider, Web3
from web3.providers.rpc import HTTPProvider

import config
import lib
from config import logging

home = expanduser("~")


class Network(object):
    def __init__(self):
        # Let's add some data to the [instance of the] class.
        self.eBlocBroker = None
        self.w3 = None
        self.oc = None


def connect():
    if config.eBlocBroker is not None and config.w3 is not None:
        return config.eBlocBroker, config.w3

    if config.w3 is None:
        try:
            config.w3 = connect_to_web3()
        except Exception as e:
            logging.error(f"E: Failed to connect web3: {e}")
            return None, None

        if not config.w3:
            return None, None

    if config.eBlocBroker is None:
        try:
            config.eBlocBroker = connect_to_eblocbroker()
        except Exception as e:
            logging.error(f"E: Failed to connect to eBlocBroker: {e}")
            return None, None

    return config.eBlocBroker, config.w3


def connect_to_web3():
    if not lib.POA_CHAIN:
        """
        * Note that you should create only one RPC Provider per process,
        * as it recycles underlying TCP/IP network connections between
        *  your process and Ethereum node
        """
        config.w3 = Web3(HTTPProvider("http://localhost:" + str(lib.RPC_PORT)))
        from web3.shh import Shh

        Shh.attach(config.w3, "shh")
    else:
        config.w3 = Web3(IPCProvider("/private/geth.ipc"))
        from web3.middleware import geth_poa_middleware

        # inject the poa compatibility middleware to the innermost layer
        config.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        # from web3.shh import Shh
        # Shh.attach(web3, 'shh')
    if not config.w3.isConnected():
        logging.error("E: If web3 is not connected please run the following: sudo chown $(whoami) /private/geth.ipc")
        return False

    return config.w3


def connect_to_eblocbroker():
    if config.w3 is None:
        config.w3 = connect_to_web3()
        if not config.w3:
            return False

    contract = json.loads(open(home + "/eBlocBroker/contractCalls/contract.json").read())
    contractAddress = contract["address"]

    with open(home + "/eBlocBroker/contractCalls/abi.json", "r") as abi_definition:
        abi = json.load(abi_definition)

    contractAddress = config.w3.toChecksumAddress(contractAddress)
    config.eBlocBroker = config.w3.eth.contract(contractAddress, abi=abi)
    return config.eBlocBroker


if __name__ == "__main__":
    eBlocBroker = connect_to_eblocbroker()

# [Errno 111] Connection refused => w3 is not connected (class.name: ConnectionRefusedError)
# Exception: w3.exceptions.BadFunctionCallOutput => wrong mapping input is give (class.name: BadFunctionCallOutput)
