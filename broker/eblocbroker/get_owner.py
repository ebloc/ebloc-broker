#!/usr/bin/env python3

import sys

import broker.eblocbroker.Contract as Contract
from broker.utils import print_tb

if __name__ == "__main__":
    Ebb: "Contract.Contract" = Contract.EBB()
    try:
        print(f"owner={Ebb.get_owner()}")
    except Exception as e:
        print_tb(e)
