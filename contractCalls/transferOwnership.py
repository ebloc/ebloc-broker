#!/usr/bin/env python3

import sys

from config import env, logging
from imports import connect
from lib import get_tx_status
from utils import _colorize_traceback


def transferOwnership(newOwner):
    eBlocBroker, w3 = connect()

    _from = w3.toChecksumAddress(env.PROVIDER_ID)
    newOwner = w3.toChecksumAddress(newOwner)
    if newOwner == "0x0000000000000000000000000000000000000000":
        logging.error("Provided address is zero")
        raise

    if not w3.isAddress(newOwner):
        logging.error("Provided address is not valid")
        raise

    if eBlocBroker.functions.getOwner().call() == newOwner:
        logging.error("newOwner is already the owner")
        raise

    try:
        tx = eBlocBroker.functions.transferOwnership(newOwner).transact({"from": _from, "gas": 4500000})
        return tx.hex()
    except Exception:
        logging.error(_colorize_traceback())
        raise


if __name__ == "__main__":
    if len(sys.argv) == 2:
        newOwner = str(sys.argv[1])
    else:
        print("Please provide the newOwner address as argument.")
        sys.exit(1)

    try:
        tx_hash = transferOwnership(newOwner)
        receipt = get_tx_status(tx_hash)
    except:
        logging.error(_colorize_traceback())
        sys.exit(1)
