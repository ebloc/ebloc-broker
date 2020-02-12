#!/usr/bin/env python3

import sys

from imports import connect


def getProviderReceiptSize(providerAddress):
    eBlocBroker, w3 = connect()
    providerAddress = w3.toChecksumAddress(providerAddress)
    return eBlocBroker.functions.getProviderReceiptSize(providerAddress).call()


if __name__ == "__main__":
    if len(sys.argv) == 2:
        providerAddress = str(sys.argv[1])
    else:
        providerAddress = "0x4e4a0750350796164D8DefC442a712B7557BF282"

    print(getProviderReceiptSize(providerAddress))
