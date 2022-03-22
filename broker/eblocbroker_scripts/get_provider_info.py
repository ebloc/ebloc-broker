#!/usr/bin/env python3

import sys

from broker import cfg
from broker._utils.tools import is_byte_str_zero, log, print_tb
from broker.config import env
from brownie.network.account import Account


def get_provider_info(self, provider):
    """Return the provider information."""
    if not isinstance(provider, Account):
        provider = self.w3.toChecksumAddress(provider)

    if not self.does_provider_exist(provider):
        raise Exception(
            f"E: Provider {provider} is not registered.\n"
            "Please try again with registered Ethereum Address as provider"
        )

    try:
        prices_set_block_numbers = self.get_provider_prices_blocks(provider)
        block_read_from, provider_price_info = self._get_provider_info(provider, prices_set_block_numbers[-1])
        _event_filter = self._eblocbroker.events.LogProviderInfo.createFilter(
            fromBlock=int(prices_set_block_numbers[0]),
            # toBlock=int(block_read_from) + 1,
            argument_filters={"provider": provider},
        )
        event_filter = {}
        for idx in range(len(_event_filter.get_all_entries()) - 1, -1, -1):
            # In lists [-1] indicated the most recent emitted event
            for key in _event_filter.get_all_entries()[idx].args:
                if key not in event_filter:
                    event_filter[key] = _event_filter.get_all_entries()[idx].args[key]

        for key in ["email", "ipfsID", "fID", "gpgFingerprint"]:
            if key not in event_filter:
                event_filter[key] = ""

        #: removes padding 24 zeros at the beginning
        gpg_fingerprint = event_filter["gpgFingerprint"].rstrip(b"\x00").hex()[24:].upper()
        provider_info = {
            "available_core_num": provider_price_info[0],
            "commitment_block_num": provider_price_info[1],
            "price_core_min": provider_price_info[2],
            "price_data_transfer": provider_price_info[3],
            "price_storage": provider_price_info[4],
            "price_cache": provider_price_info[5],
            "address": provider,
            "block_read_from": block_read_from,
            "is_orcid_verified": self.is_orcid_verified(provider),
            "email": event_filter["email"],
            "gpg_fingerprint": gpg_fingerprint,
            "f_id": event_filter["fID"],
            "ipfs_id": event_filter["ipfsID"],
        }
        orc_id = self.get_user_orcid(provider)
        if not is_byte_str_zero(orc_id):
            provider_info["orc_id"] = orc_id.decode("utf-8").replace("\x00", "")

        return provider_info
    except Exception as e:
        raise e


if __name__ == "__main__":
    Ebb = cfg.Ebb
    if len(sys.argv) == 2:
        provider = str(sys.argv[1])
    else:
        provider = env.PROVIDER_ID

    try:
        provider_info = Ebb.get_provider_info(provider)
        log(provider_info)
    except Exception as e:
        print_tb(e)
        sys.exit(1)
