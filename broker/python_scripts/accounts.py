#!/usr/bin/env python3

from brownie import accounts, history
from broker._utils._log import log
from broker._utils.tools import print_tb
from broker.errors import QuietExit


def main():
    breakpoint()  # DEBUG
    accounts
    pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except QuietExit as e:
        print(f"#> {e}")
    except Exception as e:
        print_tb(str(e))
