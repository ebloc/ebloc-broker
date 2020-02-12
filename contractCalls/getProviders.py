#!/usr/bin/env python3

import os
import sys


def getProviders(eBlocBroker=None):
    if eBlocBroker is None:
        from imports import connect_to_eblocbroker

        eBlocBroker = connect_to_eblocbroker()

    if eBlocBroker == "notconnected":
        return eBlocBroker

    return eBlocBroker.functions.getProviders().call()


if __name__ == "__main__":
    providerList = getProviders()
    if providerList == "notconnected":
        print(providerList)
        sys.exit()

    for i in range(0, len(providerList)):
        print(providerList[i])
