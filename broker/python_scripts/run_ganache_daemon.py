#!/usr/bin/env python3

import time
from contextlib import suppress

from broker import cfg
from broker.config import env
from broker.lib import run

if __name__ == "__main__":
    run(["python3", f"{env.EBLOCPATH}/_daemons/ganache_cli.py"])
    for count in range(10):
        time.sleep(2)
        with suppress(Exception):
            print(cfg.ipfs.connect_to_bootstrap_node())
            break
