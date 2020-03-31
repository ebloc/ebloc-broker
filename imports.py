#!/usr/bin/env python3

from os.path import expanduser

from web3 import IPCProvider, Web3
from web3.providers.rpc import HTTPProvider

import config
from config import EBLOCPATH, POA_CHAIN, RPC_PORT, logging
from utils import read_json

home = expanduser("~")


class Network(object):
    def __init__(self):
        # Let's add some data to the [instance of the] class.
        self.eBlocBroker = None
        self.w3 = None
        self.oc = None


def connect():
    if config.eBlocBroker and config.w3:
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
    if not POA_CHAIN:
        """
        * Note that you should create only one RPC Provider per process,
        * as it recycles underlying TCP/IP network connections between
        *  your process and Ethereum node
        """
        config.w3 = Web3(HTTPProvider(f"http://localhost:{RPC_PORT}"))
        from web3.shh import Shh

        Shh.attach(config.w3, "shh")
    else:
        config.w3 = Web3(IPCProvider("/private/geth.ipc"))
        from web3.middleware import geth_poa_middleware

        # inject the poa compatibility middleware to the innermost layer
        config.w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    if not config.w3.isConnected():
        logging.error("E: If web3 is not connected please run the following: sudo chown $(whoami) /private/geth.ipc")
        return None

    return config.w3


def connect_to_eblocbroker():
    if config.w3 is None:
        config.w3 = connect_to_web3()
        if not config.w3:
            logging.error("E: web3 is not connected")
            return False

    success, contract = read_json(f"{EBLOCPATH}/contractCalls/contract.json")
    if not success:
        logging.error("E: Couldn't read the contract.json file.")
        return None

    contract_address = contract["address"]
    success, abi = read_json(f"{EBLOCPATH}/contractCalls/abi.json")
    if not success:
        logging.error("E: Couldn't read the abi.json file")
        return None

    contract_address = config.w3.toChecksumAddress(contract_address)
    config.eBlocBroker = config.w3.eth.contract(contract_address, abi=abi)
    return config.eBlocBroker


if __name__ == "__main__":
    eBlocBroker = connect_to_eblocbroker()

# [Errno 111] Connection refused => w3 is not connected (class.name: ConnectionRefusedError)
# Exception: w3.exceptions.BadFunctionCallOutput => wrong mapping input is give (class.name: BadFunctionCallOutput)
