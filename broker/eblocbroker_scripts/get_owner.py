#!/usr/bin/env python3

from broker import cfg
from broker.utils import log, print_tb

if __name__ == "__main__":
    Ebb = cfg.Ebb
    try:
        log(f"owner={Ebb.get_owner().lower()}", "bold")
    except Exception as e:
        print_tb(e)
