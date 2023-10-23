#!/usr/bin/env python3

import sys
from contextlib import suppress

from broker import cfg, config
from broker._utils.tools import log, print_tb, read_json, run
from broker.config import env
from broker.errors import QuietExit
from broker.utils import popen_communicate, terminate


def nc(url: str, port: int):
    """Nc: arbitrary TCP and UDP connections and listens them."""
    try:
        for string in ["http://", "https://", ":8545"]:
            url = url.replace(string, "")

        run(["nc", "-v", "-w", 1, url, port])
    except Exception as e:
        raise e


def _ping(host) -> bool:
    """Return 'True' if host responds to a ping request.

    Note that that a host may not respond to a ping (ICMP) request even if the host name is valid.
    Building the command.

    Ex: "ping -c 1 google.com"
    """
    pr, output, e = popen_communicate(["ping", "-c", "1", host])  # noqa
    return pr.returncode == 0


def read_abi_file(abi_file):
    try:
        return read_json(abi_file, is_dict=False)
    except Exception as e:
        raise Exception(f"unable to read the abi.json file: {abi_file}") from e


def connect():
    """Connect to web3.

    return: ebb and web3 objects.
    """
    if config.ebb and cfg.w3:
        return config.ebb, cfg.w3, config._eblocbroker

    try:
        connect_to_eblocbroker()
    except Exception as e:
        print_tb(e)

    return config.ebb, cfg.w3, config._eblocbroker


def connect_to_eblocbroker() -> None:
    """Connect to eBlocBroker smart contract through the given private blockchain."""
    from brownie import network

    if config.ebb:
        return

    if not env.EBLOCPATH:
        raise QuietExit("env.EBLOCPATH variable is empty")

    try:
        if env.IS_EBLOCPOA:
            config.ebb = cfg.w3.eth.contract(env.CONTRACT_ADDRESS, abi=read_abi_file(env.EBB_SCRIPTS / "abi.json"))
            config._eblocbroker = config.ebb
            config.ebb.contract_address = cfg.w3.toChecksumAddress(env.CONTRACT_ADDRESS)
        elif env.IS_BLOXBERG and not cfg.IS_BROWNIE_TEST:
            try:
                network.connect(cfg.NETWORK_ID)
                if not network.is_connected():
                    log(f"E: {network.show_active()} is not connected through {env.BLOXBERG_HOST}")
                    if cfg.NETWORK_ID == "bloxberg":
                        log(f"Switch network_id={cfg.NETWORK_ID} to [blue]bloxberg_core. ", end="")
                        cfg.NETWORK_ID = "bloxberg_core"
                    elif cfg.NETWORK_ID == "bloxberg_core":
                        with suppress(Exception):
                            nc(cfg.BERG_CMPE_IP, 8545)
                            log(f"Switch network_id={cfg.NETWORK_ID} to [blue]bloxberg. ", end="")
                            cfg.NETWORK_ID = "bloxberg"

                    log(f"Trying at [blue]{cfg.NETWORK_ID}[/blue] ...")
                    network.connect(cfg.NETWORK_ID)
                    if not network.is_connected():
                        terminate(
                            f"E: {network.show_active()} is not connected through {cfg.NETWORK_ID}",
                            is_traceback=False,
                        )

                cfg.w3 = network.web3
            except:
                from broker.python_scripts import add_bloxberg_into_network_config

                add_bloxberg_into_network_config.main()
                try:
                    log(
                        "warning: [green]bloxberg[/green] key is added into the "
                        "[m]~/.brownie/network-config.yaml[/m] file. Please try again."
                    )
                    network.connect(cfg.NETWORK_ID)
                except KeyError:
                    sys.exit(1)

            from brownie import project

            project = project.load(env.CONTRACT_PROJECT_PATH)
            config.ebb = project.eBlocBroker.at(env.CONTRACT_ADDRESS)
            config.ebb.contract_address = cfg.w3.toChecksumAddress(env.CONTRACT_ADDRESS)
            #: required to fetch the contract's events
            config._eblocbroker = cfg.w3.eth.contract(
                env.CONTRACT_ADDRESS, abi=read_abi_file(env.EBB_SCRIPTS / "abi.json")
            )
            #
            config.usdtmy = project.USDTmy.at(env.TOKEN_CONTRACT_ADDRESS)
            config._usdtmy = cfg.w3.eth.contract(
                env.TOKEN_CONTRACT_ADDRESS, abi=read_abi_file(env.EBB_SCRIPTS / "abi_usdtmy.json")
            )

            from brownie import project as pro

            roc_contract_address = "0x3fb704dfDB72Fc06860D9F09124C30919488f13C"
            _project = pro.load(env.CONTRACT_PROJECT_PATH / "_other" / "roc")
            config.roc = _project.ResearchCertificate.at(roc_contract_address)
            config.roc.contract_address = cfg.w3.toChecksumAddress(roc_contract_address)
            config._roc = cfg.w3.eth.contract(roc_contract_address, abi=read_abi_file(env.EBB_SCRIPTS / "abi_roc.json"))

    except Exception as e:
        print_tb(e)
        raise e
