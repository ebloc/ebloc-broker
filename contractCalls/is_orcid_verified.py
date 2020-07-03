#!/usr/bin/env python3

import sys

from imports import connect
from utils import _colorize_traceback


def is_orcid_verified(requester):
    eBlocBroker, w3 = connect()
    return eBlocBroker.functions.isOrcIDVerified(requester).call()


if __name__ == "__main__":
    if len(sys.argv) == 2:
        requester = str(sys.argv[1])
    else:
        requester = "0x57b60037B82154eC7149142c606bA024fBb0f991"

    try:
        print(is_orcid_verified(requester))
    except:
        print(_colorize_traceback())
