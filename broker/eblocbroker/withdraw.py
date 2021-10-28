#!/usr/bin/env python3

from broker.utils import print_tb
import sys

import broker.cfg as cfg
from broker.lib import get_tx_status

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
