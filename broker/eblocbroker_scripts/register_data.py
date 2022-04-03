#!/usr/bin/env python3

from broker import cfg
from broker._utils.tools import log
from broker._utils.web3_tools import get_tx_status
from broker.config import env
from broker.errors import QuietExit
from broker.utils import print_tb


def _register_data(source_code_hash, data_price, commitment_dur):
    Ebb = cfg.Ebb
    is_exit = False
    price = None
    if not Ebb.does_provider_exist(env.PROVIDER_ID):
        log(f"warning: provider [green]{env.PROVIDER_ID}[/green] is not registered")
        raise QuietExit

    if not Ebb.is_orcid_verified(env.PROVIDER_ID):
        log(f"warning: provider [green]{env.PROVIDER_ID}[/green]'s orcid id is not authenticated yet")
        raise QuietExit

    source_code_hash_bytes = cfg.w3.toBytes(text=source_code_hash)
    try:
        (price, _commitment_dur) = cfg.Ebb.get_registered_data_prices(env.PROVIDER_ID, source_code_hash_bytes, 0)
        log(
            f"## data([green]{source_code_hash}[/green]) is already registerered.\n"
            "Use [blue]./update_data_price.py[/blue] to update its price"
        )
        is_exit = True
    except:
        pass

    if is_exit:
        raise QuietExit

    if price == data_price and _commitment_dur == commitment_dur:
        log(f"## data([green]{source_code_hash}[/green]) already registerered with the given values")
        raise QuietExit

    try:
        tx = Ebb.register_data(source_code_hash_bytes, data_price, commitment_dur)
        get_tx_status(Ebb.tx_id(tx))
    except QuietExit as e:
        raise e
    except Exception as e:
        print_tb(e)


if __name__ == "__main__":
    try:
        source_code_hash = "050e6cc8dd7e889bf7874689f1e1ead6"
        data_price = 2
        commitment_dur = 600
        _register_data(source_code_hash, data_price, commitment_dur)
    except QuietExit:
        pass
    except Exception as e:
        print_tb(e)
