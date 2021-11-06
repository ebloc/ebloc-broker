#!/usr/bin/env python3

import sys

from broker import cfg
from broker._utils.tools import log, print_tb
from broker.config import env
from brownie.network.account import Account


def pre_check_data(self):
    """Return the provider information."""
    if not isinstance(provider, Account):
        provider = self.w3.toChecksumAddress(provider)

    if not self.does_provider_exist(provider):
        raise Exception(
            f"E: Provider {provider} is not registered.\n"
            "Please try again with registered Ethereum Address as provider"
        )


def remove_data_info(self, provider):
    self.pre_check_data(provider)

    removeRegisteredData


def get_data_info(self, provider):
    self.pre_check_data(provider)
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
            log(f" * registered_data_hash={registered_data_hash}")
            (price, commitment_block_duration) = cfg.Ebb.get_registred_data_prices(provider, registered_data_hash, 0)
            provider_data[registered_data_hash] = {
                "price": price,
                "commitment_block_duration": commitment_block_duration,
            }
            log(provider_data[registered_data_hash])
            log()
    except Exception as e:
        raise e


if __name__ == "__main__":
    Ebb = cfg.Ebb
    if len(sys.argv) == 2:
        provider = str(sys.argv[1])
    else:
        provider = env.PROVIDER_ID

    try:
        data = Ebb.get_data_info(provider)
    except Exception as e:
        print_tb(e)
        sys.exit(1)
