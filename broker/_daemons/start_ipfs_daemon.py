#!/usr/bin/env python3

import time
from contextlib import suppress

from broker.config import env
from broker.lib import run
from broker.libs.ipfs import Ipfs


def _connect_to_bootstrap_node():
    ipfs = Ipfs()
    for _ in range(10):
        time.sleep(1)
        with suppress(Exception):
            print(ipfs.connect_to_bootstrap_node())
            break


if __name__ == "__main__":
    run(["python3", env.EBLOCPATH / "broker" / "_daemons" / "ipfs.py"])
    # _connect_to_bootstrap_node()
