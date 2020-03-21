#!/usr/bin/env python3

from get_providers import get_providers
import config


def getProviderPriceInfo(providerAddress, requestedCore, coreMinuteGas, gasDataTransfer):
    (blockReadFrom, coreNumber, priceCoreMin, priceDataTransfer,) = config.eBlocBroker.functions.getProviderInfo(
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
    providers = get_providers

    requestedCore = 2
    coreGasDay = 0
    coreGasHour = 0
    coreGasMin = 1
    coreMinuteGas = coreGasMin + coreGasHour * 60 + coreGasDay * 1440
    dataTransferIn = 100
    dataTransferOut = 100
    gasDataTransfer = dataTransferIn + dataTransferOut

    for provider in providers:
        print(provider)
        getProviderPriceInfo(provider, requestedCore, coreMinuteGas, gasDataTransfer)
