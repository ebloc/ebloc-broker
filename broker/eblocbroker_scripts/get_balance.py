#!/usr/bin/env python3

import sys

from broker import cfg
from broker._utils.tools import log
from broker.eblocbroker_scripts.utils import Cent


def main():
    Ebb = cfg.Ebb
    if len(sys.argv) == 2:
        address = str(sys.argv[1])
        balance = Ebb.get_balance(address)
        if balance == 0:
            log(f"[y]tokens[/y]: {Cent(balance)} cent")
        else:
            log(f"[y]tokens[/y]: {Cent(balance)} cent ≈ {Cent(balance).to('usd')} usd")

        log(f"[y]balance[/y]: {Ebb._get_balance(address)} ether")
    else:
        log("E: Provide an address as an argument")


if __name__ == "__main__":
    main()
