#!/usr/bin/env python3

import sys

from eblocbroker.Contract import Contract
from utils import _colorize_traceback

if __name__ == "__main__":
    try:
        c = Contract()
        print(f"owner={c.get_owner()}")
    except:
        _colorize_traceback()
        sys.exit(1)
