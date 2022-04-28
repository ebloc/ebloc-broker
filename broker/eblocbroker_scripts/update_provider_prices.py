#!/usr/bin/env python3

import os
import sys
from os.path import expanduser

from broker import cfg
from broker._utils._log import log
from broker._utils.tools import print_tb
from broker._utils.web3_tools import get_tx_status
from broker._utils.yaml import Yaml
from broker.config import env
from broker.errors import QuietExit


def update_provider_prices(self, available_core, commitment_blk, prices):
    """Update provider prices."""
    if commitment_blk < cfg.ONE_HOUR_BLOCK_DURATION:
        raise Exception(f"Commitment block number should be greater than {cfg.ONE_HOUR_BLOCK_DURATION}")

    if not available_core:
        raise Exception("Please enter positive value for the available core number")

    if not commitment_blk:
        raise Exception("Please enter positive value for the commitment block number")

    try:
        provider_info = self.get_provider_info(env.PROVIDER_ID)
        if (
            provider_info["price_core_min"] == prices[0]
            and provider_info["price_data_transfer"] == prices[1]
            and provider_info["price_storage"] == prices[2]
            and provider_info["price_cache"] == prices[3]
        ):
            log(provider_info)
            raise QuietExit("warning: Given information is same with the cluster's latest set prices. Nothing to do.")

        tx = self._update_provider_prices(available_core, commitment_blk, prices)
        return self.tx_id(tx)
    except Exception as e:
        raise e


if __name__ == "__main__":
    Ebb = cfg.Ebb
    yaml_fn = expanduser("~/.ebloc-broker/cfg.yaml")
    yaml_fn = expanduser(yaml_fn)
    if not os.path.exists(yaml_fn):
        log(f"E: yaml_fn({yaml_fn}) does not exist")
        raise QuietExit

    args = Yaml(yaml_fn, auto_dump=False)
    _args = args["cfg"]["provider"]
    available_core = _args["available_core"]
    commitment_blk = _args["prices"]["commitment_blk"]
    price_core_min = _args["prices"]["price_core_min"]
    price_data_transfer = _args["prices"]["price_data_transfer"]
    price_storage = _args["prices"]["price_storage"]
    price_cache = _args["prices"]["price_cache"]
    prices = [price_core_min, price_data_transfer, price_storage, price_cache]
    try:
        tx_hash = Ebb.update_provider_prices(available_core, commitment_blk, prices)
        receipt = get_tx_status(tx_hash)
    except Exception as e:
        print_tb(e)
        sys.exit(1)
