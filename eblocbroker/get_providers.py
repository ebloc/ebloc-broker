#!/usr/bin/env python3

import sys

from config import logging  # noqa: F401
from eblocbroker.Contract import Contract
from utils import _colorize_traceback

if __name__ == "__main__":
    contract = Contract()
    try:
        providers = contract.get_providers()
        if len(providers) == 0:
            print("There is not any registered provider")

        for provider in providers:
            print(provider)
    except Exception:
        _colorize_traceback()
        sys.exit(1)
