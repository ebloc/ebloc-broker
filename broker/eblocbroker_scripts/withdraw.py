#!/usr/bin/env python3

import sys

from broker import cfg
from broker._utils.web3_tools import get_tx_status
from broker.utils import print_tb

if __name__ == "__main__":
    Ebb = cfg.Ebb
    if len(sys.argv) == 2:
        account = str(sys.argv[1])
    else:
        print("Please provide an Ethereum account as an argument.")
        sys.exit(1)

    try:
        tx_hash = Ebb.withdraw(account)
        receipt = get_tx_status(tx_hash)
    except Exception as e:
        print_tb(e)
