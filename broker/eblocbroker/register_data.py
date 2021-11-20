#!/usr/bin/env python3

from broker import cfg
from broker.lib import get_tx_status
from broker.utils import print_tb


def main():
    Ebb = cfg.Ebb
    source_code_hash = "f13d75bc60898f0823566347e380a34d"
    source_code_hash_bytes = cfg.w3.toBytes(text=source_code_hash)
    data_price = 20
    commitment_block_duration = 600
    try:
        tx = Ebb.register_data(source_code_hash_bytes, data_price, commitment_block_duration)
        get_tx_status(Ebb.tx_id(tx))
    except Exception as e:
        print_tb(e)


if __name__ == "__main__":
    main()
