#!/usr/bin/env python3

import traceback

from imports import connect
from lib import get_tx_status
from settings import init_env


def updateProviderPrices(availableCoreNum, commitmentBlockNum, prices):
    eBlocBroker, w3 = connect()
    env = init_env()

    if availableCoreNum == 0:
        return (False, "Please enter positive value for the available core number")

    if commitmentBlockNum == 0:
        return (False, "Please enter positive value for the commitment block number")

    try:
        tx = eBlocBroker.functions.updateProviderPrices(availableCoreNum, commitmentBlockNum, prices).transact(
            {"from": env.PROVIDER_ID, "gas": 4500000}
        )
    except Exception:
        return False, traceback.format_exc()

    return True, tx.hex()


if __name__ == "__main__":
    availableCoreNum = 128
    commitmentBlockNum = 10
    priceCoreMin = 100
    priceDataTransfer = 1
    priceStorage = 1
    priceCache = 1
    prices = [priceCoreMin, priceDataTransfer, priceStorage, priceCache]

    success, output = updateProviderPrices(availableCoreNum, commitmentBlockNum, prices)
    if success:
        receipt = get_tx_status(success, output)
    else:
        print(output)
