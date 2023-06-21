#!/usr/bin/env python3

from broker import cfg, config
from broker._utils._log import log
from broker.utils import print_tb


def main():
    try:
        log(f"## eBlocBroker_owner={cfg.Ebb.get_owner().lower()}")
        log(f"## USDTmy_owner={config.usdtmy.getOwner().lower()}")
    except Exception as e:
        print_tb(e)


if __name__ == "__main__":
    main()
