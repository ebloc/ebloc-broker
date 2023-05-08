#!/usr/bin/env python3

import sys
from web3.logs import DISCARD

from broker import cfg
from broker._utils._log import console_ruler, log


def main():
    if len(sys.argv) == 2:
        tx_hash = str(sys.argv[1])
        event = "LogJob"
    else:
        tx_hash = "0xe7f0bdc249458d36105120cf1a0fa5036a9368c5fd13aa37448dae5993d92a33"
        event = "LogReceipt"

    tx_receipt = cfg.w3.eth.get_transaction_receipt(tx_hash)
    if event == "LogJob":
        processed_logs = cfg.Ebb.eBlocBroker.events.LogJob().processReceipt(tx_receipt, errors=DISCARD)

    if event == "LogReceipt":
        processed_logs = cfg.Ebb.eBlocBroker.events.LogReceipt().processReceipt(tx_receipt, errors=DISCARD)

    log(vars(processed_logs[0].args))
    console_ruler(character="-=", style="yellow")


if __name__ == "__main__":
    main()
