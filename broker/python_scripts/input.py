#!/usr/bin/env python3

import re

# from broker.config import env
from broker._utils.tools import print_tb
from broker.env import ENV_BASE
from broker.errors import QuietExit
from broker.utils import log
from brownie import web3

_env = ENV_BASE()


def get_valid_email(prompt):
    while True:
        email = input(prompt)
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            print("Not a valid email address")
            continue
        else:
            break

    return email


def get_valid_eth_address(prompt):
    while True:
        address = input(prompt)
        if address:
            try:
                web3.toChecksumAddress(address)
                return address
            except:
                log("not valid Ethereum address")


def main():
    if not _env.cfg["eth_address"] or _env.cfg["eth_address"] == "0x0000000000000000000000000000000000000000":
        _env.cfg["eth_address"] = get_valid_eth_address("Ethereum Address: ")
    else:
        while True:
            msg = f"==> Do you want to change Ethereum address {_env.cfg['eth_address']} [Y/n]: "
            log(msg, end="", is_write=False)
            answer = input("")
            if answer.lower() in ["y", "yes"]:
                _env.cfg["eth_address"] = get_valid_eth_address("Ethereum Address: ")
            elif answer.lower() in ["n", "no"]:
                break
            else:
                continue

            break

    if not _env.cfg["gmail"]:
        _env.cfg["gmail"] = get_valid_email("Email address: ")
    else:
        while True:
            msg = f"==> Do you want to change your gmail {_env.cfg['gmail']} [Y/n]: "
            answer = input(msg)
            if answer.lower() in ["y", "yes"]:
                _env.cfg["gmail"] = get_valid_email("Email address: ")
                break
            elif answer.lower() in ["n", "no"]:
                break
            else:
                continue


if __name__ == "__main__":
    try:
        main()
        print("\nNote that you can manually change in file ~/.ebloc-broker/cfg.yaml")
    except KeyboardInterrupt:
        pass
    except QuietExit as e:
        print(f"==> {e}")
    except Exception as e:
        print_tb(str(e))
