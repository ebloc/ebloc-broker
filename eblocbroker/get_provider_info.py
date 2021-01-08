#!/usr/bin/env python3

import sys

from config import env, logging  # noqa: F401
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
            # toBlock=int(block_read_from) + 1,
            argument_filters={"provider": str(provider)},
        )

        _event_filter = dict()
        for idx in range(len(event_filter.get_all_entries()) - 1, -1, -1):
            for key in event_filter.get_all_entries()[idx].args:
                if key not in _event_filter:
                    if event_filter.get_all_entries()[idx].args[key]:
                        _event_filter[key] = event_filter.get_all_entries()[idx].args[key]

        # In lists [-1] indicated the most recent emitted event
        provider_info = {
            "address": _provider,
            "block_read_from": block_read_from,
            "available_core_num": providerPriceInfo[0],
            "commitment_block_num": providerPriceInfo[1],
            "price_core_min": providerPriceInfo[2],
            "price_data_transfer": providerPriceInfo[3],
            "price_storage": providerPriceInfo[4],
            "price_cache": providerPriceInfo[5],
            "email": _event_filter["email"],
            "gpg_fingerprint": _event_filter["gpgFingerprint"].rstrip(b"\x00").hex(),
            "ipfs_id": _event_filter["ipfsID"],
            "f_id": _event_filter["fID"],
            "is_orcid_verified": self.is_orcid_verified(_provider),
            "whisper_id": "0x" + _event_filter["whisperID"],
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
        provider = env.PROVIDER_ID

    try:
        provider_info = Ebb.get_provider_info(provider)
        for key, value in provider_info.items():
            print("{0: <22}".format(f"{key}:") + str(value))
    except:
        _colorize_traceback()
        sys.exit(1)
