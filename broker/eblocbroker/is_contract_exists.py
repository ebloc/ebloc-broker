#!/usr/bin/env python3

import broker.eblocbroker.Contract as Contract
from broker.utils import _colorize_traceback

Ebb: "Contract.Contract" = Contract.EBB()

if __name__ == "__main__":
    try:
        print(f"is_contract_exists={Ebb.is_contract_exists()}")
    except:
        _colorize_traceback()
        print("is_contract_exists=False")
