#!/usr/bin/env python3

import sys

from utils import _colorize_traceback

if __name__ == "__main__":
    import eblocbroker.Contract as Contract

    ebb = Contract.eblocbroker

    if len(sys.argv) == 2:
        requester = str(sys.argv[1])
    else:
        requester = "0x57b60037B82154eC7149142c606bA024fBb0f991"

    try:
        print(ebb.is_orcid_verified(requester))
    except:
        _colorize_traceback()
