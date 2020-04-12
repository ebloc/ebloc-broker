#!/usr/bin/env python3

import sys

from config import logging  # noqa: F401
from config import Web3NotConnected
from imports import connect
from utils import _colorize_traceback


def get_providers():
    eBlocBroker, w3 = connect()

    try:
        return eBlocBroker.functions.getProviders().call()
    except:
        logging.error(_colorize_traceback())
        raise Web3NotConnected()


if __name__ == "__main__":
    try:
        providers = get_providers()
        for provider in providers:
            print(provider)
    except Exception:
        logging.error(_colorize_traceback())
        sys.exit(1)
