#!/usr/bin/env python3

import sys

from imports import connect_to_eblocbroker

from doesProviderExist import doesProviderExist


def getProviderReceiptNode(provider_address, index):
    eBlocBroker = connect_to_eblocbroker()
    return eBlocBroker.functions.getProviderReceiptNode(provider_address, index).call()


if __name__ == "__main__":
    if len(sys.argv) == 2:
        provider_address = str(sys.argv[1])
        print(doesProviderExist(provider_address))
    else:
        providerAddress = "0x4e4a0750350796164d8defc442a712b7557bf282"
        index = 0

    print(getProviderReceiptNode(providerAddress, index))
