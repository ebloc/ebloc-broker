#!/usr/bin/env python3

import time

from config import env
from lib import run
from libs.ipfs import connect_to_bootstrap_node

if __name__ == "__main__":
    run(["python3", f"{env.EBLOCPATH}/daemons/ganache_cli.py"])

    for count in range(10):
        time.sleep(2)
        try:
            print(connect_to_bootstrap_node())
            break
        except:
            pass
