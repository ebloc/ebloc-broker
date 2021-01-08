#!/usr/bin/env python3

import sys

from broker._utils.tools import log
from broker.eblocbroker.Contract import Contract
from broker.utils import _colorize_traceback

if __name__ == "__main__":
    contract = Contract()
    try:
        providers = contract.get_providers()
        if len(providers) == 0:
            log("E: There is no registered provider.")

        for provider in providers:
            print(provider)
    except Exception as e:
        _colorize_traceback(e)
        sys.exit(1)
