#!/usr/bin/env python3

import sys

from broker._utils.tools import print_tb
from broker.config import logging
from broker.lib import get_tx_status


def update_provider_prices(self, available_core, commitment_blk, prices):
    """Update provider prices."""
    if not available_core:
        logging.error("Please enter positive value for the available core number")
        raise

    if not commitment_blk:
        logging.error("Please enter positive value for the commitment block number")
        raise

    try:
        tx = self._update_provider_prices(available_core, commitment_blk, prices)
        return self.tx_id(tx)
    except Exception:
        logging.error(print_tb)
        raise


if __name__ == "__main__":
    import broker.eblocbroker.Contract as Contract

    Ebb: "Contract.Contract" = Contract.EBB()
    available_core = 128
    commitment_blk = 10
    price_core_min = 100
    price_data_transfer = 1
    price_storage = 1
    price_cache = 1
    prices = [price_core_min, price_data_transfer, price_storage, price_cache]

    try:
        tx_hash = Ebb.update_provider_prices(available_core, commitment_blk, prices)
        receipt = get_tx_status(tx_hash)
    except:
        print_tb()
        sys.exit(1)
