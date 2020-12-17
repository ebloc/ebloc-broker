#!/usr/bin/env python3

import sys

from broker import cfg

if __name__ == "__main__":
    Ebb = cfg.Ebb
    if len(sys.argv) == 2:
        provider_address = str(sys.argv[1])
        print(Ebb.does_provider_exist(provider_address))
    else:
        provider_address = "0x4e4a0750350796164d8defc442a712b7557bf282"
        index = 0

    print(Ebb.get_provider_receipt_node(provider_address, index))
