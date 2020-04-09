#!/usr/bin/env python3


def get_owner(eBlocBroker=None):
    if eBlocBroker is None:
        from imports import connect_to_eblocbroker

        try:
            eBlocBroker = connect_to_eblocbroker()
        except Exception:
            return None

    return eBlocBroker.functions.getOwner().call()


if __name__ == "__main__":
    print(get_owner())
