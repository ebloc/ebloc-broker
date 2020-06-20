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

    Ebb = Contract.eblocbroker

    availableCoreNum = 128
    commitmentBlockNum = 10
    price_core_min = 100
    price_data_transfer = 1
    price_storage = 1
    price_cache = 1
    prices = [price_core_min, price_data_transfer, price_storage, price_cache]

    try:
        tx_hash = Ebb.update_provider_prices(availableCoreNum, commitmentBlockNum, prices)
        receipt = get_tx_status(tx_hash)
    except:
        _colorize_traceback()
        sys.exit(1)
