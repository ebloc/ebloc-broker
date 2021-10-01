#!/usr/bin/env python3

import sys

from web3 import IPCProvider, Web3
from web3.middleware import geth_poa_middleware
from web3.providers.rpc import HTTPProvider

import broker._config as _config
import broker.cfg as cfg
import broker.config as config
from broker._utils.tools import QuietExit, log, print_tb
from broker.config import env
from broker.utils import is_geth_on, read_json, run, terminate


def connect():
    """Connect into web3 and ebloc_broker objects."""
    if config.ebb and cfg.w3:
        return config.ebb, cfg.w3, config._eBlocBroker

    try:
        if not cfg.w3.isConnected():
            connect_into_web3()

        if config.ebb is None:
            connect_to_eblocbroker()
    except Exception as e:
        print_tb(e)

    return config.ebb, cfg.w3, config._eBlocBroker


def _connect_into_web3():
    WEB3_PROVIDER_PATH = f"{env.DATADIR}/geth.ipc"
    if not env.IS_EBLOCPOA or env.IS_GETH_TUNNEL:
        if env.IS_BLOXBERG:  # https://bloxberg.org
            cfg.w3 = Web3(HTTPProvider("https://core.bloxberg.org"))
        else:
            cfg.w3 = Web3(HTTPProvider(f"http://localhost:{env.RPC_PORT}"))
        #
        # from web3.geth import shh  # does not work on > web3==5.11
        # cfg.w3.shh.attach(cfg.w3, "shh")
        # shh.attach(cfg.w3, "shh")
    else:
        cfg.w3 = Web3(IPCProvider(WEB3_PROVIDER_PATH))
        # inject the poa compatibility middleware to the innermost layer
        cfg.w3.middleware_onion.inject(geth_poa_middleware, layer=0)


def connect_into_web3():
    """Connect into web3.

    Note that you should create only one RPC Provider per process, as it
    recycles underlying TCP/IP network connections between your process and
    Ethereum node
    """
    WEB3_PROVIDER_PATH = f"{env.DATADIR}/geth.ipc"
    for _ in range(5):
        _connect_into_web3()
        if not cfg.w3.isConnected():
            try:
                if env.IS_GETH_TUNNEL:
                    raise Exception("Open tunnel: ssh -f -N -L 8545:localhost:8545 username@remote-ip")

                if not env.IS_BLOXBERG:
                    is_geth_on()
                else:
                    log("E: web3 is not connected into BLOXBERG", "red")  # delete_me
            except Exception as e:
                if type(e).__name__ != "QuietExit":
                    print_tb(e)
                else:
                    sys.exit(1)

            if not env.IS_GETH_TUNNEL and not env.IS_BLOXBERG:
                log(
                    "E: If web3 is not connected please start geth server and give permission \n"
                    "to /private/geth.ipc file doing: ",
                    end="",
                )
                log(f"sudo chown $(whoami) {WEB3_PROVIDER_PATH}", "green")
                log(f"#> Running `sudo chown $(whoami) {WEB3_PROVIDER_PATH}`")
                run(["sudo", "chown", env.WHOAMI, WEB3_PROVIDER_PATH])
        else:
            break
    else:
        terminate(is_traceback=False)
        # raise config.QuietExit()

    if not env.PROVIDER_ID:
        try:
            env.set_provider_id()
        except Exception as e:
            log(f"E' {e}")
            if type(e).__name__ != "QuietExit":
                print_tb()
            sys.exit(1)


def connect_to_eblocbroker() -> None:
    """Connect into ebloc-broker."""
    if config.ebb:
        return

    if not cfg.w3:
        cfg.w3 = connect_into_web3()

    try:
        if env.EBLOCPATH is None or env.EBLOCPATH == "":
            log("E: EBLOCPATH variable is empty")
            raise QuietExit

        if env.IS_BLOXBERG:
            json_file = f"{env.EBLOCPATH}/broker/eblocbroker/contract_bloxberg.json"
        elif env.IS_EBLOCPOA:
            json_file = f"{env.EBLOCPATH}/broker/eblocbroker/contract_eblocpoa.json"

        contract = read_json(json_file)
    except Exception as e:
        log(f"E: Couldn't read the contract.json file: {json_file}")
        print_tb(e)
        raise e

    try:  # TODO: add decoder/template for this kind of calls
        contract_address = contract["address"]
        abi_file = f"{env.EBLOCPATH}/broker/eblocbroker/abi.json"
        abi = read_json(abi_file, is_dict=False)
    except Exception as e:
        log(f"E: Couldn't read the abi.json file: {abi_file}")
        print_tb(e)
        raise e

    try:
        if env.IS_BLOXBERG:
            if not _config.IS_BROWNIE_TEST:
                from brownie import network, project

                network.connect("bloxberg")
                project = project.load("/mnt/hgfs/ebloc-broker/contract")
                config.ebb = project.eBlocBroker.at(contract_address)
                config.ebb.contract_address = cfg.w3.toChecksumAddress(contract_address)
                #: For contract events
                config._eBlocBroker = cfg.w3.eth.contract(contract_address, abi=abi)
        elif env.IS_EBLOCPOA:
            config.ebb = cfg.w3.eth.contract(contract_address, abi=abi)
            config._eBlocBroker = config.ebb
            config.ebb.contract_address = cfg.w3.toChecksumAddress(contract_address)
    except Exception as e:
        print_tb(e)
        raise e


# requests.exceptions.ConnectionError:
# [Errno 111] Connection refused => w3 is not connected (class.name: ConnectionRefusedError)
# Exception: w3.exceptions.BadFunctionCallOutput => wrong mapping input is give (class.name: BadFunctionCallOutput)
