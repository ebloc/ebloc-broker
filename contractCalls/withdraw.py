#!/usr/bin/env python3

import sys

from config import bp, logging  # noqa: F401
from imports import connect
from lib import get_tx_status
from utils import _colorize_traceback


def withdraw(account):
    try:
        eBlocBroker, w3 = connect()
        account = w3.toChecksumAddress(account)
        tx = eBlocBroker.functions.withdraw().transact({"from": account, "gas": 50000})
        return tx.hex()
    except Exception:
        logging.error(_colorize_traceback())
        raise


if __name__ == "__main__":
    if len(sys.argv) == 2:
        account = str(sys.argv[1])
    else:
        print("Please provide an Ethereum account as an argument.")
        sys.exit(1)

    try:
        tx_hash = withdraw(account)
        receipt = get_tx_status(tx_hash)
    except:
        sys.exit(1)
