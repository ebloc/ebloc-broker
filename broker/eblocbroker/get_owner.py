#!/usr/bin/env python3

import sys
import broker.eblocbroker.Contract as Contract
from broker.utils import _colorize_traceback

if __name__ == "__main__":
    Ebb = Contract.ebb()
    try:
        print(f"owner={Ebb.get_owner()}")
    except Exception as e:
        _colorize_traceback(e)
        sys.exit(1)
