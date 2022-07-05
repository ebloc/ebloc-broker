#!/usr/bin/env python3

import sys
from contextlib import suppress

from broker import cfg
from broker._utils.tools import is_byte_str_zero, log, print_tb
from broker.config import env
from broker.errors import QuietExit
from brownie.network.account import Account

Ebb = cfg.Ebb


def get_provider_info(self, provider):
    """Return the provider information."""
    if not isinstance(provider, Account):
        provider = self.w3.toChecksumAddress(provider)

    if not self.does_provider_exist(provider):
        raise QuietExit(
            f"E: provider={provider} is not registered.\n"
            f"Please try again with registered Ethereum Address as provider."
        )

    try:
        bn = Ebb.get_block_number()
        prices_set_block_numbers = self.get_provider_prices_blocks(provider)
        block_read_from, provider_prices = self._get_provider_info(provider, prices_set_block_numbers[-1])
        _event_filter = self._eblocbroker.events.LogProviderInfo.createFilter(
            fromBlock=int(prices_set_block_numbers[0]),
            # toBlock=int(block_read_from) + 1,
            argument_filters={"provider": provider},
        )
        event_filter = {}
        for idx in range(len(_event_filter.get_all_entries()) - 1, -1, -1):
            # in lists [-1] indicated the most recent emitted event
            for key in _event_filter.get_all_entries()[idx].args:
                if key not in event_filter:
                    event_filter[key] = _event_filter.get_all_entries()[idx].args[key]

        for key in ["gmail", "ipfsID", "fID", "gpgFingerprint"]:
            if key not in event_filter:
                event_filter[key] = ""

        #: removes padding 24 zeros at the beginning
        gpg_fingerprint = event_filter["gpgFingerprint"].rstrip(b"\x00").hex()[24:].upper()
        provider_info = {
            "address": provider,
            "is_orcid_verified": self.is_orcid_verified(provider),
            "gmail": event_filter["gmail"],
            "gpg_fingerprint": gpg_fingerprint,
            "f_id": event_filter["fID"],
            "ipfs_address": event_filter["ipfsID"],
            "prices_set_block_numbers": prices_set_block_numbers,
            "block_number": bn,
        }

        if bn < prices_set_block_numbers[-1]:
            remaining_blk = prices_set_block_numbers[-1] - bn
            log(f"#> remaing blocks ({remaining_blk}) for updated prices in future block: {provider_prices}")
            *_, provider_prices = Ebb._get_provider_info(provider)
            with suppress(Exception):
                provider_info["block_read_from"] = prices_set_block_numbers[-2]
        else:
            provider_info["block_read_from"] = block_read_from

        provider_info["available_core_num"] = provider_prices[0]
        provider_info["commitment_block_num"] = provider_prices[1]
        provider_info["price_core_min"] = provider_prices[2]
        provider_info["price_data_transfer"] = provider_prices[3]
        provider_info["price_storage"] = provider_prices[4]
        provider_info["price_cache"] = provider_prices[5]
        orc_id = self.get_user_orcid(provider)
        if not is_byte_str_zero(orc_id):
            provider_info["orc_id"] = orc_id.decode("utf-8").replace("\x00", "")

        return provider_info
    except Exception as e:
        raise e


def main():
    if len(sys.argv) == 2:
        provider = str(sys.argv[1])
    else:
        provider = env.PROVIDER_ID

    provider_info = Ebb.get_provider_info(provider)
    log("provider_info=", "bold", end="")
    log(provider_info)


if __name__ == "__main__":
    try:
        main()
    except QuietExit as e:
        log(e, is_wrap=True)
    except Exception as e:
        print_tb(e)
        sys.exit(1)
