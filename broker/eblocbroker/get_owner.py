#!/usr/bin/env python3

import sys

from broker.eblocbroker.Contract import Contract
from broker.utils import _colorize_traceback

if __name__ == "__main__":
    try:
        print(f"owner={Contract().get_owner()}")
    except Exception as e:
        _colorize_traceback(e)
        sys.exit(1)
