#!/usr/bin/env python3

import sys
from pprint import pprint

from web3.logs import DISCARD

import broker.cfg as cfg

if __name__ == "__main__":
    if len(sys.argv) == 2:
        tx_hash = str(sys.argv[1])
        event = "LogJob"
    else:
        tx_hash = "0xe7f0bdc249458d36105120cf1a0fa5036a9368c5fd13aa37448dae5993d92a33"
        event = "LogReceipt"

    tx_receipt = cfg.w3.eth.getTransactionReceipt(tx_hash)
    if event == "LogJob":
        processed_logs = cfg.Ebb.eBlocBroker.events.LogJob().processReceipt(tx_receipt, errors=DISCARD)
        pprint(vars(processed_logs[0].args))
        print("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")

    if event == "LogReceipt":
        processed_logs = cfg.Ebb.eBlocBroker.events.LogReceipt().processReceipt(tx_receipt, errors=DISCARD)
        pprint(vars(processed_logs[0].args))
        print("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
