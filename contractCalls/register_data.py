#!/usr/bin/env python3

import sys
import traceback

from imports import connect
from lib import get_tx_status
from settings import init_env
from utils import _colorize_traceback

env = init_env()


def register_data(sourceCodeHash, price, commitmentBlockDuration):
    eBlocBroker, w3 = connect()
    try:
        tx = eBlocBroker.functions.registerData(sourceCodeHash, price, commitmentBlockDuration).transact(
            {"from": env.PROVIDER_ID, "gas": 100000}
        )
        return tx.hex()
    except Exception:
        print(_colorize_traceback())
        traceback.format_exc()
        raise


if __name__ == "__main__":
    sourceCodeHash = "0x68b8d8218e730fc2957bcb12119cb204"
    try:
        tx_hash = register_data(sourceCodeHash, 20, 240)
        receipt = get_tx_status(tx_hash)
    except:
        print(_colorize_traceback())
        sys.exit(1)
