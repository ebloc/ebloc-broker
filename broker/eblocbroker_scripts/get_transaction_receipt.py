#!/usr/bin/env python3

import sys
from contextlib import suppress

from broker import cfg
from broker._utils.tools import log

Ebb = cfg.Ebb


def get_msg_value(block_hash, tx_index):
    tx_by_block = Ebb.get_transaction_by_block(block_hash, tx_index)
    return float(tx_by_block["value"]) / 10**9


def merge_two_dicts(x, y):
    """Given two dictionaries, merge them into a new dict as a shallow copy."""
    z = x.copy()
    z.update(y)
    return z


def get_transaction_receipt(tx_hash, only_receipt=False):
    try:
        tx_receipt = Ebb.get_transaction_receipt(tx_hash)
        tx_by_block = Ebb.get_transaction_by_block(tx_receipt["blockHash"].hex(), tx_receipt["transactionIndex"])
        merged = merge_two_dicts(tx_receipt, tx_by_block)
        with suppress(Exception):
            log(f"is_tx_passed={bool(tx_receipt['status'])}")

        log(merged)
        msg_value = get_msg_value(tx_receipt["blockHash"].hex(), tx_receipt["transactionIndex"])
        if msg_value > 0:
            print()
            print(f"msg_value={msg_value}")
        return merged
    except Exception as e:
        log(f"E: [g]{e}")


def main():
    if len(sys.argv) == 2:
        tx_hash = str(sys.argv[1])
    else:  # dummy tx-hash exists on bloxberg
        tx_hash = "0xa980242a427de1906067b3b277f101066bf470215a9821399ea0e0eed56282d1"

    get_transaction_receipt(tx_hash)


if __name__ == "__main__":
    main()
