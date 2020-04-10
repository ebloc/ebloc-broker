#!/usr/bin/env python3

import traceback

from web3 import IPCProvider, Web3
from web3.providers.rpc import HTTPProvider

import _utils.colorer  # noqa: F401
import config
from config import bp, logging  # noqa: F401
from settings import init_env
from utils import read_json


class Network(object):
    def __init__(self):
        # let's add some data to the [instance of the] class.
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
    env = init_env()

    if not env.POA_CHAIN:
        """
        * Note that you should create only one RPC Provider per process,
        * as it recycles underlying TCP/IP network connections between
        *  your process and Ethereum node
        """
        config.w3 = Web3(HTTPProvider(f"http://localhost:{env.RPC_PORT}"))
        from web3.shh import Shh

        Shh.attach(config.w3, "shh")
    else:
        config.w3 = Web3(IPCProvider("/private/geth.ipc"))
        from web3.middleware import geth_poa_middleware

        # inject the poa compatibility middleware to the innermost layer
        config.w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    if not config.w3.isConnected():
        logging.error(
            "E: If web3 is not connected please start geth server and run the following: sudo chown $(whoami) /private/geth.ipc"
        )
        return None

    if not env.PROVIDER_ID:
        env.set_provider_id()
    return config.w3


def connect_to_eblocbroker():
    env = init_env()
    if config.w3 is None:
        try:
            config.w3 = connect_to_web3()
        except:
            logging.error("E: Web3 is not connected")
            logging.error(traceback.format_exc())
            raise

    try:
        contract = read_json(f"{env.EBLOCPATH}/contractCalls/contract.json")
    except:
        logging.error("E: Couldn't read the contract.json file.")
        logging.error(traceback.format_exc())
        raise

    contract_address = contract["address"]
    try:  # TODO: add decoder/template for this kind of call
        abi = read_json(f"{env.EBLOCPATH}/contractCalls/abi.json")
    except:
        logging.error("E: Couldn't read the abi.json file")
        logging.error(traceback.format_exc())
        raise

    contract_address = config.w3.toChecksumAddress(contract_address)
    config.eBlocBroker = config.w3.eth.contract(contract_address, abi=abi)
    return config.eBlocBroker


if __name__ == "__main__":
    eBlocBroker = connect_to_eblocbroker()

# [Errno 111] Connection refused => w3 is not connected (class.name: ConnectionRefusedError)
# Exception: w3.exceptions.BadFunctionCallOutput => wrong mapping input is give (class.name: BadFunctionCallOutput)
