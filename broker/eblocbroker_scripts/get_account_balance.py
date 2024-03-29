#!/usr/bin/env python3

import sys

from broker import cfg
from broker._utils.tools import log
from broker.utils import print_tb


def main():
    Ebb = cfg.Ebb
    if len(sys.argv) == 2:
        address = str(sys.argv[1])
        log(f"{Ebb._get_balance(address)} ether")
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
