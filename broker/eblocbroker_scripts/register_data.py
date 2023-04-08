#!/usr/bin/env python3

from broker import cfg
from broker._utils.tools import log
from broker._utils.web3_tools import get_tx_status
from broker.config import env
from broker.eblocbroker_scripts.get_data_price import get_latest_data_price
from broker.eblocbroker_scripts.utils import Cent
from broker.errors import QuietExit
from broker.utils import print_tb


def _register_data(code_hash, data_price, commitment_dur):
    Ebb = cfg.Ebb
    is_exit = False
    price = None
    is_update = False
    if not Ebb.does_provider_exist(env.PROVIDER_ID):
        log(f"warning: provider [g]{env.PROVIDER_ID}[/g] is not registered")
        raise QuietExit

    if not Ebb.is_orcid_verified(env.PROVIDER_ID):
        log(f"warning: provider [g]{env.PROVIDER_ID}[/g]'s orcid id is not authenticated yet")
        raise QuietExit

    if commitment_dur < cfg.ONE_HOUR_BLOCK_DURATION:
        log(f"warning: commitment block number should be greater than {cfg.ONE_HOUR_BLOCK_DURATION}")
        raise QuietExit

    code_hash_bytes = cfg.w3.toBytes(text=code_hash)
    try:
        (price, _commitment_dur) = get_latest_data_price(env.PROVIDER_ID, code_hash_bytes, is_verbose=False)
        try:
            bn = cfg.Ebb.get_registered_data_bn(env.PROVIDER_ID, code_hash_bytes)
            if bn[0] == 0:
                log(f"E: registered block number returns zero for {code_hash_bytes}")
                is_exit = True

            # "\nUse [blue]./update_data_price.py[/blue] to update its price"
            log(
                f"## data([g]{code_hash}[/g]) is already registerered with price={Cent(price)._to()} usd ",
                end="",
            )
            if price == 1:
                log("and costs nothing", "b")
            else:
                log()

            if data_price == price or (price == 1 and data_price == 0):
                is_exit = True
            else:
                log(f"## updating data price with price={data_price}")
                is_update = True
        except Exception as e:
            print_tb(e)
    except:
        pass

    if is_exit:
        raise QuietExit

    if price == data_price and _commitment_dur == commitment_dur:
        log(f"## data([g]{code_hash}[/g]) is already registerered with the given values")
        raise QuietExit

    if price == 1 and data_price == 0 and _commitment_dur == commitment_dur:
        log(f"## data([g]{code_hash}[/g]) is already registerered with the given values")
        raise QuietExit

    try:
        if is_update:
            tx = Ebb.update_data_price(code_hash_bytes, data_price, commitment_dur)
        else:
            tx = Ebb.register_data(code_hash_bytes, data_price, commitment_dur)

        get_tx_status(Ebb.tx_id(tx))
    except QuietExit as e:
        raise e
    except Exception as e:
        print_tb(e)


def main():
    try:
        code_hash = "fe801973c5b22ef6861f2ea79dc1eb9d"
        data_price = 1
        commitment_dur = 600
        _register_data(code_hash, data_price, commitment_dur)
    except QuietExit:
        pass
    except Exception as e:
        print_tb(e)


if __name__ == "__main__":
    main()
