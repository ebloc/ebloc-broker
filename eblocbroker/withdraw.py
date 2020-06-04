#!/usr/bin/env python3

import sys

from config import logging
from lib import get_tx_status

if __name__ == "__main__":
    import eblocbroker.Contract as Contract

    ebb = Contract.eblocbroker

    if len(sys.argv) == 2:
        account = str(sys.argv[1])
    else:
        print("Please provide an Ethereum account as an argument")
        sys.exit(1)

    try:
        tx_hash = ebb.withdraw(account)
        receipt = get_tx_status(tx_hash)
    except:
        sys.exit(1)
