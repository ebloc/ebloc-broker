#!/usr/bin/env python3

import sys

from config import env, logging
from lib import get_tx_status
from utils import _colorize_traceback


def update_provider_prices(self, availableCoreNum, commitmentBlockNum, prices):
    if not availableCoreNum:
        logging.error("Please enter positive value for the available core number")
        raise

    if not commitmentBlockNum:
        logging.error("Please enter positive value for the commitment block number")
        raise

    try:
        tx = self.eBlocBroker.functions.updateProviderPrices(availableCoreNum, commitmentBlockNum, prices).transact(
            {"from": env.PROVIDER_ID, "gas": 4500000}
        )
        return tx.hex()
    except Exception:
        logging.error(_colorize_traceback)
        raise


if __name__ == "__main__":
    import eblocbroker.Contract as Contract

    ebb = Contract.eblocbroker

    availableCoreNum = 128
    commitmentBlockNum = 10
    priceCoreMin = 100
    priceDataTransfer = 1
    priceStorage = 1
    priceCache = 1
    prices = [priceCoreMin, priceDataTransfer, priceStorage, priceCache]

    try:
        tx_hash = ebb.update_provider_prices(availableCoreNum, commitmentBlockNum, prices)
        receipt = get_tx_status(tx_hash)
    except:
        _colorize_traceback()
        sys.exit(1)
