#!/usr/bin/env python3

from broker import cfg
from broker.utils import log, print_tb


def is_contract_exists():
    try:
        Ebb = cfg.Ebb
    except Exception as e:
        print_tb(e)

    log(f"==> is_contract_exists={Ebb.is_contract_exists()}", "bold")


if __name__ == "__main__":
    is_contract_exists()
