#!/usr/bin/env python3

import sys, os


def getProviders(eBlocBroker=None):
    if eBlocBroker is None:
        from imports import connectEblocBroker

        eBlocBroker = connectEblocBroker()

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
