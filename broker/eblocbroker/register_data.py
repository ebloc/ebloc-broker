#!/usr/bin/env python3

import sys

from broker.lib import get_tx_status
from broker.utils import print_tb

if __name__ == "__main__":
    import broker.eblocbroker.Contract as Contract

    Ebb: "Contract.Contract" = Contract.EBB()
    source_code_hash = "0x68b8d8218e730fc2957bcb12119cb204"
    try:
        tx_hash = Ebb.register_data(source_code_hash, 20, 240)
        tx_receipt = get_tx_status(tx_hash)
    except:
        print_tb()
        sys.exit(1)
