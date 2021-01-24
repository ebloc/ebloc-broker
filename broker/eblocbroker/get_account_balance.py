#!/usr/bin/env python3

import sys

from broker._utils.tools import log
from broker.eblocbroker.Contract import Contract

if __name__ == "__main__":
    if len(sys.argv) == 2:
        address = str(sys.argv[1])
        print(Contract()._get_balance(address))
    else:
        log("E: Please provide an address as argument")
