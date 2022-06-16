#!/usr/bin/env python3

from broker import cfg
from broker._utils.tools import log
from broker._utils.web3_tools import get_tx_status
from broker.config import env
from broker.eblocbroker_scripts.get_data_price import get_latest_data_price
from broker.errors import QuietExit
from broker.utils import print_tb


def _register_data(source_code_hash, data_price, commitment_dur):
    Ebb = cfg.Ebb
    is_exit = False
    price = None
    is_update = False
    if not Ebb.does_provider_exist(env.PROVIDER_ID):
        log(f"warning: provider [green]{env.PROVIDER_ID}[/green] is not registered")
        raise QuietExit

    if not Ebb.is_orcid_verified(env.PROVIDER_ID):
        log(f"warning: provider [green]{env.PROVIDER_ID}[/green]'s orcid id is not authenticated yet")
        raise QuietExit

    code_hash_bytes = cfg.w3.toBytes(text=source_code_hash)
    try:
        (price, _commitment_dur) = get_latest_data_price(env.PROVIDER_ID, code_hash_bytes, is_verbose=False)
        bn = cfg.Ebb.get_registered_data_bn(env.PROVIDER_ID, code_hash_bytes)
        if bn[0] == 0:
            log(f"E: registered block number returns zero for {code_hash_bytes}")
            is_exit = True

        log(
            f"## data([green]{source_code_hash}[/green]) is already registerered"
            # "\nUse [blue]./update_data_price.py[/blue] to update its price"
        )
        if data_price == price:
            is_exit = True
        else:
            log("## Update price")
            is_update = True
    except Exception as e:
        print_tb(e)
        breakpoint()  # DEBUG

    if is_exit:
        raise QuietExit

    if price == data_price and _commitment_dur == commitment_dur:
        log(f"## data([green]{source_code_hash}[/green]) already registerered with the given values")
        raise QuietExit

    try:
        if not is_update:
            tx = Ebb.register_data(code_hash_bytes, data_price, commitment_dur)
        else:
            tx = Ebb.update_data_price(code_hash_bytes, data_price, commitment_dur)

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
