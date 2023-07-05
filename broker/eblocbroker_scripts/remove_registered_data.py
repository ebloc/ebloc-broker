#!/usr/bin/env python3

from broker import cfg
from broker._utils.tools import log
from broker._utils.web3_tools import get_tx_status
from broker.config import env
from broker.eblocbroker_scripts.data import is_data_registered, pre_check_data
from broker.utils import print_tb

Ebb = cfg.Ebb


def main():
    provider = env.PROVIDER_ID
    pre_check_data(provider)
    data_hash = b"f13d75bc60898f0823566347e380a34d"
    try:
        if is_data_registered(provider, data_hash):
            tx = Ebb.remove_registered_data(data_hash)
            get_tx_status(Ebb.tx_id(tx))
        else:
            log(f"==> data({data_hash}) is deleted or not registered")
    except Exception as e:
        print_tb(e)


if __name__ == "__main__":
    main()
