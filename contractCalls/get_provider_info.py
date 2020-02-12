#!/usr/bin/env python3

import sys

from imports import connect


def get_provider_info(_provider, eBlocBroker=None, w3=None):
    eBlocBroker, w3 = connect()
    if eBlocBroker is None or w3 is None:
        return

    provider = w3.toChecksumAddress(_provider)

    if not eBlocBroker.functions.doesProviderExist(provider).call():
        print(
            "Provider("
            + provider
            + ") is not registered. Please try again with registered Ethereum Address as provider."
        )
        sys.exit()

    blockReadFrom, providerPriceInfo = eBlocBroker.functions.getProviderInfo(provider, 0).call()
    event_filter = eBlocBroker.events.LogProviderInfo.createFilter(
        fromBlock=int(blockReadFrom), toBlock=int(blockReadFrom) + 1, argument_filters={"provider": str(provider)}
    )

    provider_info = {
        "blockReadFrom": blockReadFrom,
        "availableCoreNum": providerPriceInfo[0],
        "commitmentBlockNum": providerPriceInfo[1],
        "priceCoreMin": providerPriceInfo[2],
        "priceDataTransfer": providerPriceInfo[3],
        "priceStorage": providerPriceInfo[4],
        "priceCache": providerPriceInfo[5],
        "email": event_filter.get_all_entries()[-1].args["email"],  # -1 indicated the most recent emitted evet
        "miniLockID": event_filter.get_all_entries()[-1].args["miniLockID"],
        "ipfsID": event_filter.get_all_entries()[-1].args["ipfsID"],
        "fID": event_filter.get_all_entries()[-1].args["fID"],
        "whisperID": "0x" + event_filter.get_all_entries()[-1].args["whisperID"],
    }

    return True, provider_info


if __name__ == "__main__":
    if len(sys.argv) == 2:
        provider = str(sys.argv[1])
    else:
        provider = "0x57b60037b82154ec7149142c606ba024fbb0f991"

    status, provider_info = get_provider_info(provider)

    if status:
        print(
            "{0: <20}".format("blockReadFrom: ")
            + str(provider_info["blockReadFrom"])
            + "\n"
            + "{0: <20}".format("availableCoreNum: ")
            + str(provider_info["availableCoreNum"])
            + "\n"
            + "{0: <20}".format("priceCoreMin: ")
            + str(provider_info["priceCoreMin"])
            + "\n"
            + "{0: <20}".format("priceDataTransfer: ")
            + str(provider_info["priceDataTransfer"])
            + "\n"
            + "{0: <20}".format("priceStorage: ")
            + str(provider_info["priceStorage"])
            + "\n"
            + "{0: <20}".format("priceCache: ")
            + str(provider_info["priceCache"])
            + "\n"
            + "{0: <20}".format("commitmentBlockNum: ")
            + str(provider_info["commitmentBlockNum"])
            + "\n"
            + "{0: <20}".format("email: ")
            + provider_info["email"]
            + "\n"
            + "{0: <20}".format("miniLockID: ")
            + provider_info["miniLockID"]
            + "\n"
            + "{0: <20}".format("ipfsID: ")
            + provider_info["ipfsID"]
            + "\n"
            + "{0: <20}".format("fID: ")
            + provider_info["fID"]
            + "\n"
            + "{0: <20}".format("whisperID: ")
            + provider_info["whisperID"]
        )
