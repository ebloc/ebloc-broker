#!/usr/bin/env python3

import sys

from config import env, logging
from imports import connect
from lib import get_tx_status
from utils import _colorize_traceback


def updateProviderPrices(availableCoreNum, commitmentBlockNum, prices):
    eBlocBroker, w3 = connect()

    if availableCoreNum == 0:
        logging.error("Please enter positive value for the available core number")
        raise

    if commitmentBlockNum == 0:
        logging.error("Please enter positive value for the commitment block number")
        raise

    try:
        tx = eBlocBroker.functions.updateProviderPrices(availableCoreNum, commitmentBlockNum, prices).transact(
            {"from": env.PROVIDER_ID, "gas": 4500000}
        )
        return tx.hex()
    except Exception:
        logging.error(_colorize_traceback)
        raise


if __name__ == "__main__":
    availableCoreNum = 128
    commitmentBlockNum = 10
    priceCoreMin = 100
    priceDataTransfer = 1
    priceStorage = 1
    priceCache = 1
    prices = [priceCoreMin, priceDataTransfer, priceStorage, priceCache]

    try:
        tx_hash = updateProviderPrices(availableCoreNum, commitmentBlockNum, prices)
        receipt = get_tx_status(tx_hash)
    except:
        logging.error(_colorize_traceback())
        sys.exit(1)
