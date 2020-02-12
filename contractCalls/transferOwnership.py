#!/usr/bin/env python3

import sys
import traceback

import lib
from imports import connect


def transferOwnership(newOwner, eBlocBroker=None, w3=None):
    eBlocBroker, w3 = connect()
    _from = w3.toChecksumAddress(lib.PROVIDER_ID)
    newOwner = w3.toChecksumAddress(newOwner)

    if eBlocBroker is None or w3 is None:
        return False, "web3 is notconnected."

    if newOwner == "0x0000000000000000000000000000000000000000":
        return False, "Provided address is zero."

    if not w3.isAddress(newOwner):
        return False, "Provided address is not valid."

    if eBlocBroker.functions.getOwner().call() == newOwner:
        return False, "newOwner is already the owner"

    try:
        tx = eBlocBroker.functions.transferOwnership(newOwner).transact({"from": _from, "gas": 4500000})
    except Exception:
        return False, traceback.format_exc()

    return True, tx.hex()


if __name__ == "__main__":
    if len(sys.argv) == 2:
        newOwner = str(sys.argv[1])
        status, result = transferOwnership(newOwner)
        if status:
            print("tx_hash=" + result)
        else:
            print(result)
    else:
        print("Please provide the newOwner address as argument.")
