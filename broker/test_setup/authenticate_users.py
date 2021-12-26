#!/usr/bin/env python3

from broker import cfg
from broker._utils.tools import print_tb
from broker._utils.web3_tools import get_tx_status
from broker.test_setup._users import users

Ebb = cfg.Ebb


def main():
    owner_address = Ebb.get_owner()
    for user in users:
        try:
            tx_hash = Ebb.authenticate_orc_id(user, "0000-0001-7642-0552", owner_address)
            if tx_hash:
                get_tx_status(tx_hash)
        except Exception as e:
            print_tb(e)


if __name__ == "__main__":
    main()
