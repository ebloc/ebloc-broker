#!/usr/bin/env python3

import sys


def isOrcIDVerified(requesterAddress, eBlocBroker=None):
    if eBlocBroker is None:
        from imports import connect_to_eblocbroker

        try:
            eBlocBroker = connect_to_eblocbroker()
        except Exception:
            return None

    if not eBlocBroker.functions.isOrcIDVerified(requester).call():
        return False
    else:
        return True


if __name__ == "__main__":
    if len(sys.argv) == 2:
        requester = str(sys.argv[1])
    else:
        requester = "0x57b60037B82154eC7149142c606bA024fBb0f991"

    print(isOrcIDVerified(requester))
