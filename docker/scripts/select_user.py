#!/usr/bin/env python3

from random import shuffle

from broker import cfg
from broker.env import ENV_BASE
from broker.test_setup.user_set import requesters

_env = ENV_BASE()


def main():
    if not _env.cfg["eth_address"] or _env.cfg["eth_address"] == "0x0000000000000000000000000000000000000000":
        shuffle(requesters)
        for idx, user in enumerate(requesters):
            output = cfg.Ebb.get_provider_info(user)
            if not output["ipfs_address"]:
                _env.cfg["eth_address"] = user
                print(f"Selected provider={user}")
                break


if __name__ == "__main__":
    main()
