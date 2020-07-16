#!/usr/bin/env python3

import sys

from config import logging  # noqa: F401
from utils import _colorize_traceback


def get_provider_info(self, _provider):
    provider = self.w3.toChecksumAddress(_provider)
    if not self.eBlocBroker.functions.doesProviderExist(provider).call():
        logging.error(
            f"\nE: Provider {provider} is not registered."
            "\nPlease try again with registered Ethereum Address as provider."
        )
        raise

    try:
        block_read_from, providerPriceInfo = self.eBlocBroker.functions.getProviderInfo(provider, 0).call()
        event_filter = self.eBlocBroker.events.LogProviderInfo.createFilter(
            fromBlock=int(block_read_from),
            toBlock=int(block_read_from) + 1,
            argument_filters={"provider": str(provider)},
        )
        # In lists [-1] indicated the most recent emitted event
        provider_info = {
            "block_read_from": block_read_from,
            "available_core_num": providerPriceInfo[0],
            "commitment_block_num": providerPriceInfo[1],
            "price_core_min": providerPriceInfo[2],
            "price_data_transfer": providerPriceInfo[3],
            "price_storage": providerPriceInfo[4],
            "price_cache": providerPriceInfo[5],
            "email": event_filter.get_all_entries()[-1].args["email"],
            "gpg_fingerprint": event_filter.get_all_entries()[-1].args["gpgFingerprint"].rstrip(b"\x00").hex(),
            "ipfs_id": event_filter.get_all_entries()[-1].args["ipfsID"],
            "f_id": event_filter.get_all_entries()[-1].args["fID"],
            "whisper_id": "0x" + event_filter.get_all_entries()[-1].args["whisperID"],
            "is_orcid_verified": self.is_orcid_verified(_provider),
        }
        return provider_info
    except:
        _colorize_traceback()
        raise


if __name__ == "__main__":
    from eblocbroker.Contract import Contract

    Ebb = Contract()

    if len(sys.argv) == 2:
        provider = str(sys.argv[1])
    else:
        provider = "0x57b60037b82154ec7149142c606ba024fbb0f991"

    try:
        provider_info = Ebb.get_provider_info(provider)
        for key, value in provider_info.items():
            print("{0: <22}".format(f"{key}:") + str(value))
    except:
        _colorize_traceback()
        sys.exit(1)
