#!/usr/bin/env python3

import sys

from broker import cfg
from broker._utils.tools import log


def main():
    Ebb = cfg.Ebb
    if len(sys.argv) == 2:
        address = str(sys.argv[1])
        log(Ebb._get_balance(address))
    else:
        log("E: Please provide an address as argument")


if __name__ == "__main__":
    main()
