#!/usr/bin/env python3

import sys

from imports import connect_to_web3
from utils import is_transaction_passed

if __name__ == "__main__":
    if len(sys.argv) == 2:
        tx_hash = str(sys.argv[1])
    else:
        print("Please provide transaction hash as an argument")
        sys.exit(1)

    w3 = connect_to_web3()
    if w3 is None:
        sys.exit(1)

    print(f"is_transaction_passed={is_transaction_passed(tx_hash)}")
