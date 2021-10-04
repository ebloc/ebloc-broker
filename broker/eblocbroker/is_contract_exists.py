#!/usr/bin/env python3

import broker.cfg as cfg
from broker.utils import print_tb

if __name__ == "__main__":
    try:
        Ebb = cfg.Ebb
        print(f"is_contract_exists={Ebb.is_contract_exists()}")
    except:
        print_tb()
        print("E: is_contract_exists=False")
