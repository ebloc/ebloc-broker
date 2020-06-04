#!/usr/bin/env python3

from web3 import IPCProvider, Web3
from web3.geth import shh
from web3.middleware import geth_poa_middleware
from web3.providers.rpc import HTTPProvider

import _utils.colorer  # noqa: F401
import config
from config import env, logging
from startup import bp  # noqa: F401
from utils import _colorize_traceback, read_json


def connect():
    if config.eBlocBroker and config.w3:
        return config.eBlocBroker, config.w3

    if config.w3 is None:
        config.w3 = connect_to_web3()

    if config.eBlocBroker is None:
        try:
            config.eBlocBroker = connect_to_eblocbroker()
        except Exception as e:
            raise Exception("E: Problem on web3 connection") from e

    return config.eBlocBroker, config.w3


def connect_to_web3():
    if config.w3:
        return config.w3

    if not env.POA_CHAIN:
        """
        Note that you should create only one RPC Provider per process,
        as it recycles underlying TCP/IP network connections between
        your process and Ethereum node
        """
        config.w3 = Web3(HTTPProvider(f"http://localhost:{env.RPC_PORT}"))
        config.w3.shh.attach(config.w3, "shh")
        shh.attach(config.w3, "shh")
    else:
        config.w3 = Web3(IPCProvider("/private/geth.ipc"))
        # inject the poa compatibility middleware to the innermost layer
        config.w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    if not config.w3.isConnected():
        logging.error(
            "E: If web3 is not connected please start geth server and run the following:\n"
            "sudo chown $(whoami) /private/geth.ipc"
        )
        raise config.Web3NotConnected()

    if not env.PROVIDER_ID:
        env.set_provider_id()

    return config.w3


def connect_to_eblocbroker():
    if config.eBlocBroker:
        return config.eBlocBroker

    if config.w3 is None:
        config.w3 = connect_to_web3()

    try:
        contract = read_json(f"{env.EBLOCPATH}/eblocbroker/contract.json")
    except:
        logging.error("E: Couldn't read the contract.json file")
        raise

    try:  # TODO: add decoder/template for this kind of call
        contract_address = contract["address"]
        abi = read_json(f"{env.EBLOCPATH}/eblocbroker/abi.json", is_dict=False)
    except:
        logging.error("E: Couldn't read the abi.json file")
        _colorize_traceback()
        raise

    try:
        contract_address = config.w3.toChecksumAddress(contract_address)
        config.eBlocBroker = config.w3.eth.contract(contract_address, abi=abi)
        return config.eBlocBroker
    except:
        logging.error("E: Couldn't retrieve eBlocBroker contract")
        raise


# requests.exceptions.ConnectionError:
# [Errno 111] Connection refused => w3 is not connected (class.name: ConnectionRefusedError)
# Exception: w3.exceptions.BadFunctionCallOutput => wrong mapping input is give (class.name: BadFunctionCallOutput)
