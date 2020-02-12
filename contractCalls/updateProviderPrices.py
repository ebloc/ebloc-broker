#!/usr/bin/env python3

import json
import os
import pprint
import sys
from os.path import expanduser

from imports import connect_to_eblocbroker, connect_to_web3

home = expanduser("~")


def updateProviderPrices(availableCoreNum, commitmentBlockNum, prices, eBlocBroker=None, w3=None):
    if w3 is None:
        w3 = connect_to_web3()
        if not w3:
            return

    if eBlocBroker is None:
        eBlocBroker = connect_to_eblocbroker(w3)

    PROVIDER_ID = w3.toChecksumAddress(os.getenv("PROVIDER_ID"))

    if availableCoreNum == 0:
        return (False, "Please enter positive value for the available core number")

    if commitmentBlockNum == 0:
        return (False, "Please enter positive value for the commitment block number")

    try:
        tx = eBlocBroker.functions.updateProviderPrices(availableCoreNum, commitmentBlockNum, prices).transact(
            {"from": PROVIDER_ID, "gas": 4500000}
        )
    except Exception:
        return False, traceback.format_exc()

    return True, tx.hex()


if __name__ == "__main__":
    w3 = connect_to_web3()
    availableCoreNum = 128
    commitmentBlockNum = 10
    priceCoreMin = 100
    priceDataTransfer = 1
    priceStorage = 1
    priceCache = 1
    prices = [priceCoreMin, priceDataTransfer, priceStorage, priceCache]

    status, result = updateProviderPrices(availableCoreNum, commitmentBlockNum, prices, None, w3)
    if status:
        print("Tx_hash: " + result)
        receipt = w3.eth.waitForTransactionReceipt(result)
        print("Transaction receipt mined: \n")
        pprint.pprint(dict(receipt))
        print("Was transaction successful?")
        pprint.pprint(receipt["status"])
    else:
        print(result)
