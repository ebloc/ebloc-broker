#!/usr/bin/env python3

from utils import log


def get_provider_price_info(address, requested_core, core_minute, data_transfer):
    provider_info = Ebb.get_provider_info(address)
    availabe_core_num = provider_info["available_core_num"]
    price_core_min = provider_info["price_core_min"]
    price_data_transfer = provider_info["price_data_transfer"]

    print("{0: <19}".format("core_number: ") + str(availabe_core_num))
    print("{0: <19}".format("price_core_min: ") + str(price_core_min))
    print("{0: <19}".format("price_data_transfer: ") + str(price_data_transfer))
    if requested_core > availabe_core_num:
        print("{0: <19}".format("price: ") + "Requested core is greater than provider's core")
    else:
        _price = requested_core * core_minute * price_core_min + data_transfer * price_data_transfer
        print("{0: <19}".format("price: ") + str(_price))


if __name__ == "__main__":
    import eblocbroker.Contract as Contract

    Ebb = Contract.eblocbroker

    providers = Ebb.get_providers()
    requested_core = 2
    day = 0
    hour = 0
    minute = 1
    core_minute = minute + hour * 60 + day * 1440
    data_transfer_in = 100
    data_transfer_out = 100
    data_transfer = data_transfer_in + data_transfer_out
    for provider in providers:
        log(f"==> provider_address={provider}")
        get_provider_price_info(provider, requested_core, core_minute, data_transfer)
