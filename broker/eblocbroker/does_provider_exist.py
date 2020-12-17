#!/usr/bin/env python3

import sys

from broker import cfg

if __name__ == "__main__":
    Ebb = cfg.Ebb
    if len(sys.argv) == 2:
        provider_address = str(sys.argv[1])
        print(Ebb.does_provider_exist(provider_address))
    else:
        print("E: Provide provider address as and argument.")
