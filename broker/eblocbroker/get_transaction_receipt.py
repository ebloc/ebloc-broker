#!/usr/bin/env python3

import sys

from broker.utils import print_tb

if __name__ == "__main__":
    import broker.eblocbroker.Contract as Contract

    Ebb: "Contract.Contract" = Contract.EBB()
    if len(sys.argv) == 2:
        tx = str(sys.argv[1])
    else:
        tx = "0xfa65c8516e81f972d1bdf801e0524aad1b2a9c54bb8e746613fb7316034f3e3e"

    try:
        print(Ebb.get_transaction_receipt(tx))
        # print(getTransactionReceipt(tx)['blockNumber'])
    except:
        print_tb()
        sys.exit(1)
