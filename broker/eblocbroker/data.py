#!/usr/bin/env python3

import sys
from contextlib import suppress

from broker import cfg
from broker._utils.tools import log, print_tb
from broker.config import env
from brownie.network.account import Account

Ebb = cfg.Ebb


def pre_check_data(provider):
    """Return the provider information."""
    if not isinstance(provider, Account):
        provider = Ebb.w3.toChecksumAddress(provider)

    if not Ebb.does_provider_exist(provider):
        raise Exception(
            f"E: Provider {provider} is not registered.\n"
            "Please try again with registered Ethereum Address as provider"
        )


def remove_data_info(provider, _hash):
    pre_check_data(provider)
    Ebb.remove_registered_data(_hash)


def get_data_info(self, provider):
    pre_check_data(provider)
    try:
        prices_set_block_numbers = self.get_provider_prices_blocks(provider)
        genesis_block = int(prices_set_block_numbers[0])
        event_filter = self._eBlocBroker.events.LogRegisterData.createFilter(
            fromBlock=genesis_block,
            toBlock="latest",
            argument_filters={"provider": provider},
        )
        provider_data = {}
        for entry in event_filter.get_all_entries():
            registered_data_hash = entry.args["registeredDataHash"]
            with suppress(Exception):
                # ignores removed data
                (price, commitment_block_duration) = cfg.Ebb.get_registred_data_prices(
                    provider, registered_data_hash, 0
                )
                log(f" * registered_data_hash={registered_data_hash}")
                provider_data[registered_data_hash] = {
                    "price": price,
                    "commitment_block_duration": commitment_block_duration,
                }
                log(provider_data[registered_data_hash])
                log()
    except Exception as e:
        raise e


if __name__ == "__main__":
    if len(sys.argv) == 2:
        provider = str(sys.argv[1])
    else:
        provider = env.PROVIDER_ID

    try:
        data = Ebb.get_data_info(provider)
        # remove_data_info(provider, b"f13d75bc60898f0823566347e380a34d")
    except Exception as e:
        print_tb(e)
        sys.exit(1)
