#!/usr/bin/env python3

import sys
from os.path import expanduser
from pathlib import Path
from broker import cfg
from broker._utils.tools import log
from broker.utils import print_tb

# Ebb = cfg.Ebb


def main():
    Ebb = cfg.Ebb
    if len(sys.argv) == 2:
        address = str(sys.argv[1])

        _base_account = address.replace("0x", "")
        fn = str(Path(expanduser("~/.brownie/accounts")) / _base_account)
        _base_account = Ebb.brownie_load_account(fn, "alper")

        to_account = "0xd118b6ef83ccf11b34331f1e7285542ddf70bc49"

        log(f"{Ebb._get_balance(address)} ether")
        tx = Ebb.transfer("0.49 ether", _base_account, to_account, required_confs=1)
        log(tx)
    else:
        log("E: Please provide an address as argument")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print_tb(e)
        print()
        log(str(e))
        breakpoint()  # DEBUG
