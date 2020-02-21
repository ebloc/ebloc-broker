#!/usr/bin/env python3

import sys
import traceback

from imports import connect
from lib import get_tx_status


def withdraw(account):
    eBlocBroker, w3 = connect()
    account = w3.toChecksumAddress(account)
    try:
        tx = eBlocBroker.functions.withdraw().transact({"from": account, "gas": 50000})
    except Exception:
        return False, traceback.format_exc()

    return True, tx.hex()


if __name__ == "__main__":
    if len(sys.argv) == 2:
        account = str(sys.argv[1])
    else:
        print("Please provide an Ethereum account as an argument.")
        sys.exit()

    status, result = withdraw(account)
    if status:
        receipt = get_tx_status(status, result)
    else:
        print(result)
