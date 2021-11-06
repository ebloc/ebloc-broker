#!/usr/bin/env python3

import sys

from broker import cfg

if __name__ == "__main__":
    Ebb = cfg.Ebb
    if len(sys.argv) == 2:
        providerAddress = str(sys.argv[1])
    else:
        providerAddress = "0x4e4a0750350796164D8DefC442a712B7557BF282"

    print(Ebb.get_provider_receipt_size(providerAddress))
