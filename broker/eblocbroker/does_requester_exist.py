#!/usr/bin/env python3

import sys

if __name__ == "__main__":
    from broker.eblocbroker.Contract import Contract

    if len(sys.argv) == 2:
        requester = str(sys.argv[1])
    else:
        requester = "0x57b60037B82154eC7149142c606bA024fBb0f991"

    print(Contract().does_requester_exist(requester))
