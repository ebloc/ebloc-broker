#!/usr/bin/env python3

import sys

from broker._utils.tools import _colorize_traceback
from broker.config import logging
from broker.lib import get_tx_status


def update_provider_prices(self, availableCoreNum, commitmentBlockNum, prices):
    """Update provider prices."""
    if not availableCoreNum:
        logging.error("Please enter positive value for the available core number")
        raise

    if not commitmentBlockNum:
        logging.error("Please enter positive value for the commitment block number")
        raise

    try:
        tx = self._update_provider_prices(availableCoreNum, commitmentBlockNum, prices)
        return self.tx_id(tx)
    except Exception:
        logging.error(_colorize_traceback)
        raise


if __name__ == "__main__":
    import broker.eblocbroker.Contract as Contract

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
