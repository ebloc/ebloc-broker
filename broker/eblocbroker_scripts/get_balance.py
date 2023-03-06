#!/usr/bin/env python3

import sys

from broker import cfg
from broker._utils.tools import log
from broker.eblocbroker_scripts.utils import Cent


def main():
    if len(sys.argv) == 2:
        address = str(sys.argv[1])
        balance = cfg.Ebb.get_balance(address)
        print(f"{Cent(balance)} cent ≈ {Cent(balance).to('usd')} usd")
    else:
        log("E: Provide an address as an argument")


if __name__ == "__main__":
    main()
