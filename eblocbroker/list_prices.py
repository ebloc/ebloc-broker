#!/usr/bin/env python3

import config


def get_provider_price_info(providerAddress, requestedCore, coreMinuteGas, gasDataTransfer):
    (blockReadFrom, coreNumber, price_core_min, price_data_transfer,) = config.Ebb.functions.getProviderInfo(
        providerAddress
    ).call()

    print("{0: <19}".format("coreNumber: ") + str(coreNumber))
    print("{0: <19}".format("price_core_min: ") + str(price_core_min))
    print("{0: <19}".format("price_data_transfer: ") + str(price_data_transfer))
    if requestedCore > coreNumber:
        print("{0: <19}".format("price: ") + "Requested core is greater than provider's core")
    else:
        print(
            "{0: <19}".format("price: ")
            + str(requestedCore * coreMinuteGas * price_core_min + gasDataTransfer * price_data_transfer)
        )


if __name__ == "__main__":
    import eblocbroker.Contract as Contract

    Ebb = Contract.eblocbroker

    providers = Ebb.get_providers()

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
        get_provider_price_info(provider, requestedCore, coreMinuteGas, gasDataTransfer)
