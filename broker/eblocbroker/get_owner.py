#!/usr/bin/env python3

import broker.cfg as cfg
from broker.utils import print_tb

if __name__ == "__main__":
    Ebb = cfg.Ebb
    try:
        print(f"owner={Ebb.get_owner()}")
    except Exception as e:
        print_tb(e)
