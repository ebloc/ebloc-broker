#!/usr/bin/env python3

import sys

from broker import cfg
from broker._utils.tools import log

if __name__ == "__main__":
    Ebb = cfg.Ebb
    if len(sys.argv) == 2:
        tx = str(sys.argv[1])
    else:
        tx = "0xa980242a427de1906067b3b277f101066bf470215a9821399ea0e0eed56282d1"

    try:
        log(Ebb.get_transaction_receipt(tx))
    except Exception as e:
        log(f"E: {e}")
