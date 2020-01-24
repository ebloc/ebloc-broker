#!/usr/bin/env python3

import sys


def getProviderReceiptSize(providerAddress, eBlocBroker=None, web3=None):
    if eBlocBroker is None and web3 is None:
        import os
        from imports import connectEblocBroker, getWeb3

        web3 = getWeb3()
        eBlocBroker = connectEblocBroker(web3)

    providerAddress = web3.toChecksumAddress(providerAddress)
    return eBlocBroker.functions.getProviderReceiptSize(providerAddress).call()


if __name__ == "__main__":
    if len(sys.argv) == 2:
        providerAddress = str(sys.argv[1])
    else:
        providerAddress = "0x4e4a0750350796164D8DefC442a712B7557BF282"

    print(getProviderReceiptSize(providerAddress))
