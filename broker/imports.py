#!/usr/bin/env python3

import sys

from web3 import IPCProvider, Web3
from web3.middleware import geth_poa_middleware
from web3.providers.rpc import HTTPProvider

from broker import cfg, config
from broker._utils.tools import log, print_tb, read_json
from broker.config import env
from broker.errors import QuietExit
from broker.python_scripts import add_bloxberg_into_network_config
from broker.utils import is_geth_on, run, terminate


def read_abi_file():
    try:
        abi_file = env.EBB_SCRIPTS / "abi.json"
        return read_json(abi_file, is_dict=False)
    except Exception as e:
        raise Exception(f"unable to read the abi.json file: {abi_file}") from e


def connect():
    """Connect to Web3.

    return: ebb and web3 objects.
    """
    if config.ebb and cfg.w3:
        return config.ebb, cfg.w3, config._eblocbroker

    try:
        connect_to_web3()
        connect_to_eblocbroker()
    except Exception as e:
        print_tb(e)

    return config.ebb, cfg.w3, config._eblocbroker


def _connect_to_web3() -> None:
    """Connect to web3 of the ethereum blockchain.

    * bloxberg:
    __ https://bloxberg.org
    """
    if env.IS_GETH_TUNNEL or not env.IS_EBLOCPOA:
        if env.IS_BLOXBERG:
            cfg.w3 = Web3(HTTPProvider("https://core.bloxberg.org"))
        else:
            cfg.w3 = Web3(HTTPProvider(f"http://localhost:{env.RPC_PORT}"))
    else:
        cfg.w3 = Web3(IPCProvider(env.DATADIR.joinpath("geth.ipc")))
        #: inject the poa compatibility middleware to the innermost layer
        cfg.w3.middleware_onion.inject(geth_poa_middleware, layer=0)


def connect_to_web3() -> None:
    """Connect to private ethereum network using web3.

    Note that you should create only one RPC Provider per process, as it
    recycles underlying TCP/IP network connections between your process and
    Ethereum node
    """
    if cfg.w3.isConnected():
        return

    web3_ipc_fn = env.DATADIR.joinpath("geth.ipc")
    for _ in range(5):
        _connect_to_web3()
        if not cfg.w3.isConnected():
            try:
                if env.IS_GETH_TUNNEL:
                    raise Exception("Web3ConnectError: try tunnelling: ssh -f -N -L 8545:localhost:8545 username@<ip>")

                if env.IS_BLOXBERG:
                    log("E: web3 is not connected into [green]BLOXBERG[/green]")
                else:
                    is_geth_on()
            except QuietExit:
                pass
            except Exception as e:
                print_tb(e)
                sys.exit(1)

            if not env.IS_GETH_TUNNEL and not env.IS_BLOXBERG:
                log(
                    "E: If web3 is not connected please start geth server and give permission \n"
                    "to /private/geth.ipc file doing: ",
                    end="",
                )
                log(f"sudo chown $(logname) {web3_ipc_fn}", "green")
                log(f"#> running `sudo chown $(whoami) {web3_ipc_fn}`")
                run(["sudo", "chown", env.WHOAMI, web3_ipc_fn])
        else:
            break
    else:
        terminate(is_traceback=False)


def connect_to_eblocbroker() -> None:
    """Connect to eBlocBroker smart contract in the given private blockchain."""
    if config.ebb:
        return

    if not cfg.w3:
        connect_to_web3()

    if not env.EBLOCPATH:
        log("E: env.EBLOCPATH variable is empty")
        raise QuietExit

    try:
        if env.IS_EBLOCPOA:
            config.ebb = cfg.w3.eth.contract(env.CONTRACT_ADDRESS, abi=read_abi_file())
            config._eblocbroker = config.ebb
            config.ebb.contract_address = cfg.w3.toChecksumAddress(env.CONTRACT_ADDRESS)
        elif env.IS_BLOXBERG and not cfg.IS_BROWNIE_TEST:
            from brownie import network, project

            try:
                network.connect("bloxberg")
            except:
                add_bloxberg_into_network_config.main()
                try:
                    log(
                        "warning: [green]bloxberg[/green] key is added into the "
                        "[m]~/.brownie/network-config.yaml[/m] file. Please try again."
                    )
                    network.connect("bloxberg")
                except KeyError:
                    sys.exit(1)

            project = project.load(env.CONTRACT_PROJECT_PATH)
            config.ebb = project.eBlocBroker.at(env.CONTRACT_ADDRESS)
            config.ebb.contract_address = cfg.w3.toChecksumAddress(env.CONTRACT_ADDRESS)
            #: required for to fetch the contract's events
            config._eblocbroker = cfg.w3.eth.contract(env.CONTRACT_ADDRESS, abi=read_abi_file())
    except Exception as e:
        print_tb(e)
        raise e
