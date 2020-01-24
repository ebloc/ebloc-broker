#!/usr/bin/env python3


def get_owner(eBlocBroker=None):
    if eBlocBroker is None:
        from imports import connectEblocBroker

        eBlocBroker = connectEblocBroker()
        if not eBlocBroker:
            return False

    return eBlocBroker.functions.getOwner().call()


if __name__ == "__main__":
    print(get_owner())
