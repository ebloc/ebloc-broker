#!/usr/bin/env python3

from contextlib import suppress

from broker import cfg
from broker._utils.web3_tools import get_tx_status
from broker._utils.yaml import Yaml
from broker.test_setup.user_set import users


def main():
    yaml_fn = "~/ebloc-broker/broker/test_setup/requester.yaml"
    for user in users:
        yaml_user = Yaml(yaml_fn)
        yaml_user["cfg"]["eth_address"] = user
        with suppress(Exception):
            tx_hash = cfg.Ebb.register_requester(yaml_fn, is_question=False)
            if tx_hash:
                get_tx_status(tx_hash)


if __name__ == "__main__":
    main()
