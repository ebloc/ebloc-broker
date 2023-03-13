#!/usr/bin/env python3

from broker.utils import print_tb
import sys
import time
from broker import cfg
from broker._utils.tools import log


def main():
    Ebb = cfg.Ebb
    if len(sys.argv) == 2:
        address = str(sys.argv[1])
        log(f"{Ebb._get_balance(address)} ether")
        time.sleep(2)
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
