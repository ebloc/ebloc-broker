#!/usr/bin/env python3

import broker.eblocbroker.Contract as Contract
from broker.utils import print_tb

Ebb: "Contract.Contract" = Contract.EBB()

if __name__ == "__main__":
    try:
        print(f"is_contract_exists={Ebb.is_contract_exists()}")
    except:
        print_tb()
        print("is_contract_exists=False")
