#!/usr/bin/env python3

import sys

from broker import cfg
from broker._utils.tools import log


def main():
    if len(sys.argv) == 2:
        address = str(sys.argv[1])
        print(cfg.Ebb.get_balance(address))
    else:
        log("E: Provide an address as an argument")


if __name__ == "__main__":
    main()
