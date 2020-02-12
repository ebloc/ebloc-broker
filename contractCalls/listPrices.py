#!/usr/bin/env python3

import os
import sys


def getProviders(eBlocBroker=None):
    if eBlocBroker is None:
        from imports import connect_to_eblocbroker

        eBlocBroker = connect_to_eblocbroker()

    if eBlocBroker == "notconnected":
        return eBlocBroker
    return eBlocBroker.functions.getProviders().call(), eBlocBroker


def getProviderPriceInfo(providerAddress, requestedCore, coreMinuteGas, gasDataTransfer):
    blockReadFrom, coreNumber, priceCoreMin, priceDataTransfer = eBlocBroker.functions.getProviderInfo(
        providerAddress
    ).call()

    print("{0: <19}".format("coreNumber: ") + str(coreNumber))
    print("{0: <19}".format("priceCoreMin: ") + str(priceCoreMin))
    print("{0: <19}".format("priceDataTransfer: ") + str(priceDataTransfer))
    if requestedCore > coreNumber:
        print("{0: <19}".format("price: ") + "Requested core is greater than provider's core")
    else:
        print(
            "{0: <19}".format("price: ")
            + str(requestedCore * coreMinuteGas * priceCoreMin + gasDataTransfer * priceDataTransfer)
        )


if __name__ == "__main__":
    providerList, eBlocBroker = getProviders()
    if providerList == "notconnected":
        print(providerList)
        sys.exit()

    requestedCore = 2
    coreGasDay = 0
    coreGasHour = 0
    coreGasMin = 1
    coreMinuteGas = coreGasMin + coreGasHour * 60 + coreGasDay * 1440
    dataTransferIn = 100
    dataTransferOut = 100
    gasDataTransfer = dataTransferIn + dataTransferOut

    for i in range(0, len(providerList)):
        print(providerList[i])
        getProviderPriceInfo(providerList[i], requestedCore, coreMinuteGas, gasDataTransfer)

        if i != len(providerList) - 1:
            print("")
