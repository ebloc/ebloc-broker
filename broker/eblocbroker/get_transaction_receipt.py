#!/usr/bin/env python3

import sys

from broker import cfg
from broker._utils.tools import log
from broker.utils import print_tb

if __name__ == "__main__":
    Ebb = cfg.Ebb
    if len(sys.argv) == 2:
        tx = str(sys.argv[1])
    else:
        tx = "0xfa65c8516e81f972d1bdf801e0524aad1b2a9c54bb8e746613fb7316034f3e3e"

    try:
        log(Ebb.get_transaction_receipt(tx))
    except:
        print_tb()
        sys.exit(1)
