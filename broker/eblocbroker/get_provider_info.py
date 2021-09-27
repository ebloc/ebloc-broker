#!/usr/bin/env python3

import sys

from broker._utils.tools import _colorize_traceback, log
from broker.config import env, logging
from brownie.network.account import Account


def get_provider_info(self, provider, index=0):
    """Return the provider information."""
    if not isinstance(provider, Account):
        provider = self.w3.toChecksumAddress(provider)

    try:
        if not self.does_provider_exist(provider):
            logging.error(
                f"\nE: Provider {provider} is not registered."
                "\nPlease try again with registered Ethereum Address as provider."
            )
            raise
    except Exception as e:
        _colorize_traceback(e)
        log(
            "Warning: Could not interact with/call the contract function.\n"
            "Is contract deployed correctly and chain synced?"
        )
        raise e

    try:
        block_read_from, provider_price_info = self._get_provider_info(provider, index=index)
        event_filter = self._eBlocBroker.events.LogProviderInfo.createFilter(
            fromBlock=int(block_read_from),
            # toBlock=int(block_read_from) + 1,
            argument_filters={"provider": provider},
        )
        _event_filter = dict()
        for idx in range(len(event_filter.get_all_entries()) - 1, -1, -1):
            # In lists [-1] indicated the most recent emitted event
            for key in event_filter.get_all_entries()[idx].args:
                if key not in _event_filter:
                    if event_filter.get_all_entries()[idx].args[key]:
                        _event_filter[key] = event_filter.get_all_entries()[idx].args[key]

        keys = ["email", "gpgFingerprint", "fID", "ipfsID"]
        for key in keys:
            try:
                _event_filter[key]
            except:
                _event_filter[key] = ""

        provider_info = {
            "address": provider,
            "block_read_from": block_read_from,
            "available_core_num": provider_price_info[0],
            "commitment_block_num": provider_price_info[1],
            "price_core_min": provider_price_info[2],
            "price_data_transfer": provider_price_info[3],
            "price_storage": provider_price_info[4],
            "price_cache": provider_price_info[5],
            "is_orcid_verified": self.is_orcid_verified(provider),
            "email": _event_filter["email"],
            "gpg_fingerprint": _event_filter["gpgFingerprint"].rstrip(b"\x00").hex(),
            "f_id": _event_filter["fID"],
            "ipfs_id": _event_filter["ipfsID"],
        }
        return provider_info
    except Exception as e:
        raise e


if __name__ == "__main__":
    import broker.eblocbroker.Contract as Contract

    Ebb: "Contract.Contract" = Contract.EBB()
    if len(sys.argv) == 2:
        provider = str(sys.argv[1])
    else:
        provider = env.PROVIDER_ID

    try:
        provider_info = Ebb.get_provider_info(provider)
        for key, value in provider_info.items():
            print("{0: <22}".format(f"{key}:") + str(value))
    except Exception as e:
        _colorize_traceback(e)
        sys.exit(1)
