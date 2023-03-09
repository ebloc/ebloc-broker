#!/usr/bin/env python3

from broker import cfg
from broker._utils.tools import log
from broker._utils.web3_tools import get_tx_status
from broker.config import env
from broker.errors import QuietExit
from broker.utils import print_tb


def _update_data_price():
    Ebb = cfg.Ebb
    if not Ebb.does_provider_exist(env.PROVIDER_ID):
        log(f"warning: Provider {env.PROVIDER_ID} is not registered.\n")
        raise QuietExit

    code_hash = "050e6cc8dd7e889bf7874689f1e1ead6"
    new_data_price = 20
    commitment_block_duration = 600
    code_hash_bytes = cfg.w3.toBytes(text=code_hash)
    try:
        (price, _commitment_block_duration) = cfg.Ebb.get_registered_data_price(env.PROVIDER_ID, code_hash_bytes, 0)
        if price == new_data_price and _commitment_block_duration == commitment_block_duration:
            log(f"## data([g]{code_hash}[/g]) already registerered with the given values")
            raise QuietExit
    except Exception as e:
        raise QuietExit from e

    try:
        tx = Ebb.update_data_price(code_hash_bytes, new_data_price, commitment_block_duration)
        get_tx_status(Ebb.tx_id(tx))
    except QuietExit:
        pass
    except Exception as e:
        print_tb(e)


if __name__ == "__main__":
    try:
        _update_data_price()
    except QuietExit:
        pass
    except Exception as e:
        print_tb(e)
