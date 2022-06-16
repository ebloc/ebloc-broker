#!/usr/bin/env python3

import sys

from broker import cfg
from broker._utils.tools import log

Ebb = cfg.Ebb


def get_msg_value(block_hash, tx_index):
    tx_by_block = Ebb.get_transaction_by_block(block_hash, tx_index)
    return float(tx_by_block["value"]) / 10**9


def main():
    if len(sys.argv) == 2:
        tx = str(sys.argv[1])
    else:
        tx = "0xa980242a427de1906067b3b277f101066bf470215a9821399ea0e0eed56282d1"

    try:
        tx_receipt = Ebb.get_transaction_receipt(tx)
        log(tx_receipt)

        tx_by_block = Ebb.get_transaction_by_block(tx_receipt["blockHash"].hex(), tx_receipt["transactionIndex"])
        log(tx_by_block)
        print(get_msg_value(tx_receipt["blockHash"].hex(), tx_receipt["transactionIndex"]))

    except Exception as e:
        log(f"E: {e}")


if __name__ == "__main__":
    main()
