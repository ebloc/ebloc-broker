#!/usr/bin/env python3

import sys


def get_providers(eBlocBroker=None):
    if eBlocBroker is None:
        from imports import connect_to_eblocbroker

        eBlocBroker = connect_to_eblocbroker()

    if not eBlocBroker:
        return None

    return eBlocBroker.functions.getProviders().call()


if __name__ == "__main__":
    providers = get_providers()
    if not providers:
        print(providers)
        sys.exit(1)

    for provider in providers:
        print(provider)
