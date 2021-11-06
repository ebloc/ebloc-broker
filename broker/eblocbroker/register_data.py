#!/usr/bin/env python3

import sys
from broker import cfg
from broker.lib import get_tx_status
from broker.utils import print_tb

if __name__ == "__main__":
    Ebb = cfg.Ebb
    source_code_hash = "0x68b8d8218e730fc2957bcb12119cb204"
    data_price = 20
    commitment_block_duration = 600
    try:
        tx_hash = Ebb.register_data(source_code_hash, data_price, commitment_block_duration)
        tx_receipt = get_tx_status(tx_hash)
    except:
        print_tb()
        sys.exit(1)
