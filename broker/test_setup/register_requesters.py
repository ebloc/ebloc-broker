#!/usr/bin/env python3

import sys

from broker import cfg
from broker._utils.web3_tools import get_tx_status
from broker._utils.yaml import Yaml
from broker.test_setup.user_set import requesters
from broker.utils import print_tb


def main():
    yaml_fn = "~/ebloc-broker/broker/test_setup/requester.yaml"
    for idx, user in enumerate(requesters):
        yaml_user = Yaml(yaml_fn)
        yaml_user["cfg"]["eth_address"] = user
        try:
            #: could also be used for updating requesters as well
            print(f"[  counter={idx}  ] user={user}")
            tx_hash = cfg.Ebb.register_requester(yaml_fn, is_question=False)
            if tx_hash:
                get_tx_status(tx_hash)
        except Exception as e:
            print_tb(e)
            sys.exit(1)


if __name__ == "__main__":
    main()
