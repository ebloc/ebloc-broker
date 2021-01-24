#!/usr/bin/env python3

import sys

from broker._utils.tools import log
from broker.config import setup_logger
from broker.eblocbroker.Contract import Contract
from broker.utils import _colorize_traceback

logging = setup_logger()


if __name__ == "__main__":
    Ebb = Contract()
    is_write_to_file = False
    if len(sys.argv) == 2:
        is_write_to_file = sys.argv[1]
        if is_write_to_file in ("1", "True", "true"):
            is_write_to_file = True

    try:
        output = Ebb.get_block_number()
        if is_write_to_file:
            print(output)
        else:
            log(f"block_number={output}")
    except Exception:
        _colorize_traceback()

    sys.exit(0)
