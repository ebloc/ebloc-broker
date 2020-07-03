#!/usr/bin/env python3

import sys

from eblocbroker.Contract import Contract
from utils import _colorize_traceback

if __name__ == "__main__":
    try:
        print(f"owner={Contract().get_owner()}")
    except:
        _colorize_traceback()
        sys.exit(1)
