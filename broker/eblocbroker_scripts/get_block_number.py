#!/usr/bin/env python3

import sys

from broker import cfg
from broker._utils.tools import log
from broker.config import env, setup_logger
from broker.utils import print_tb

Ebb = cfg.Ebb
logging = setup_logger()


def get_block_number(is_write_to_file=False):
    try:
        output = Ebb.get_block_number()
        if is_write_to_file:
            env.config["block_continue"] = output
            #: used in cleaning for a new test
            env.config["token_balance"] = int(Ebb.get_balance(env.PROVIDER_ID))
        else:
            log(f"block_number={output} | active_network={env.ACTIVE_NETWORK}")
    except Exception as e:
        print_tb(e)


def main():
    is_write_to_file = False
    if len(sys.argv) == 2:
        if sys.argv[1] in ("1", "True", "true", "t", "T"):
            is_write_to_file = True

    get_block_number(is_write_to_file)


if __name__ == "__main__":
    main()
