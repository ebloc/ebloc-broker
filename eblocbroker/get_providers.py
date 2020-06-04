#!/usr/bin/env python3

import sys

from config import logging  # noqa: F401
from eblocbroker.Contract import Contract
from utils import _colorize_traceback

if __name__ == "__main__":
    contract = Contract()
    try:
        providers = contract.get_providers()
        for provider in providers:
            print(provider)
    except Exception:
        _colorize_traceback()
        sys.exit(1)
