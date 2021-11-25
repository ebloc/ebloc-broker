#!/usr/bin/env python3

from broker import cfg
from broker._utils.tools import log
from broker.config import env
from broker.errors import QuietExit
from broker.lib import get_tx_status
from broker.utils import print_tb


def _register_data(yaml_fn=""):
    Ebb = cfg.Ebb

    if not Ebb.does_provider_exist(env.PROVIDER_ID):
        log(f"Warning: Provider {env.PROVIDER_ID} is not registered.\n")
        raise QuietExit

    source_code_hash = "b6aaf03752dc68d625fc57b451faa2bf"
    data_price = 20
    commitment_block_duration = 600
    source_code_hash_bytes = cfg.w3.toBytes(text=source_code_hash)
    is_exit = False
    try:
        (price, _commitment_block_duration) = cfg.Ebb.get_registered_data_prices(
            env.PROVIDER_ID, source_code_hash_bytes, 0
        )
        log(
            f"## data([green]{source_code_hash}[/green]) is already registerered.\n"
            "Use [blue]./update_data_price.py[/blue] to update its prices."
        )
        is_exit = True
    except:
        pass

    if is_exit:
        raise QuietExit

    if price == data_price and _commitment_block_duration == commitment_block_duration:
        log(f"## data([green]{source_code_hash}[/green]) already registerered with the given values")
        raise QuietExit

    try:
        tx = Ebb.register_data(source_code_hash_bytes, data_price, commitment_block_duration)
        get_tx_status(Ebb.tx_id(tx))
    except QuietExit:
        pass
    except Exception as e:
        print_tb(e)


if __name__ == "__main__":
    try:
        _register_data()
    except QuietExit:
        pass
    except Exception as e:
        print_tb(e)
