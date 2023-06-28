#!/usr/bin/env python3

import sys

from broker._utils.yaml import Yaml
from broker.eblocbroker_scripts.register_provider import register_provider_wrapper
from broker.test_setup.user_set import requesters
from broker.utils import print_tb


def main():
    yaml_fn = "~/ebloc-broker/broker/test_setup/requester_docker.yaml"
    for idx, user in enumerate(requesters):
        yaml_user = Yaml(yaml_fn)
        yaml_user["cfg"]["eth_address"] = user
        try:
            print(f"[  counter={idx}  ] provider={user}")
            register_provider_wrapper(yaml_fn, is_bare=True)
        except Exception as e:
            print_tb(e)
            sys.exit(1)


if __name__ == "__main__":
    main()
