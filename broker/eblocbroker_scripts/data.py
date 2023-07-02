#!/usr/bin/env python3

import sys
from contextlib import suppress

from broker import cfg
from broker._utils.tools import log, print_tb
from broker.config import env
from broker.errors import QuietExit
from brownie.network.account import Account

Ebb = cfg.Ebb


def pre_check_data(provider):
    """Return the provider's information."""
    if not isinstance(provider, Account):
        provider = Ebb.w3.toChecksumAddress(provider)

    if not Ebb.does_provider_exist(provider):
        raise Exception(
            f"E: Provider {provider} is not registered.\n"
            "Please try again with registered Ethereum Address as provider"
        )


def is_data_registered(provider, registered_data_hash) -> bool:
    if not isinstance(registered_data_hash, bytes):
        raise QuietExit(f"==> requested data={registered_data_hash} is not in `bytes` instance")

    with suppress(Exception):
        cfg.Ebb.get_registered_data_price(provider, registered_data_hash, 0)
        return True

    return False


def data_output_verbose(provider_data):
    """Print only data hash and its price without color."""
    print()
    print("data_hash, price")
    for k, v in sorted(provider_data.items()):
        print(f"{k.decode('utf-8')}, {v['price']}")


def get_data_info(self, provider) -> None:
    pre_check_data(provider)
    try:
        prices_set_block_numbers = self.get_provider_prices_blocks(provider)
        event_filter = self._eblocbroker.events.LogRegisterData.createFilter(
            fromBlock=int(prices_set_block_numbers[0]),
            toBlock="latest",
            argument_filters={"provider": provider},
        )
        provider_data = {}
        for entry in event_filter.get_all_entries():
            registered_data_hash = entry.args["registeredDataHash"]
            with suppress(Exception):  # ignores removed data hashes
                (price, commitment_block_duration) = cfg.Ebb.get_registered_data_price(
                    provider, registered_data_hash, 0
                )
                provider_data[registered_data_hash] = {
                    "commitment_block_duration": commitment_block_duration,
                    "price": price,
                    "registered_block_number": entry["blockNumber"],
                }

        for k, v in sorted(provider_data.items()):
            log(f" * registered_data_hash={k.decode('utf-8')}")
            log(f"\t{v}")

        # data_output_verbose(provider_data)
    except Exception as e:
        raise e


def main():
    if len(sys.argv) == 2:
        provider = str(sys.argv[1])
    else:
        provider = env.PROVIDER_ID

    try:
        Ebb.get_data_info(provider)
    except Exception as e:
        print_tb(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
