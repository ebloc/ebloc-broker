#!/usr/bin/env python3

import time

from broker.config import env
from broker.lib import run
from broker.libs.ipfs import Ipfs

if __name__ == "__main__":
    run(["python3", f"{env.EBLOCPATH}/broker/daemons/ipfs.py"])
    for count in range(10):
        time.sleep(2)
        try:
            ipfs = Ipfs()
            print(ipfs.connect_to_bootstrap_node())
            break
        except:
            pass
