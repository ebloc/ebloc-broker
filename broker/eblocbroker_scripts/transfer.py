#!/usr/bin/env python3

# Example usage: ./transfer.py 0xa9fc23943e48a3efd35bbdd440932f123d05b697 "1 usd"

import sys

from broker import cfg
from broker._utils.tools import log, print_tb
from broker._utils.web3_tools import get_tx_status
from broker.eblocbroker_scripts.utils import Cent

Ebb = cfg.Ebb


def transfer_all_to_owner(self, _from, amount, is_verbose=True):
    """Transfer all tokens to the owner of the contract."""
    amount = cfg.Ebb.get_balance(_from)
    if is_verbose:
        log(f"balance_before_transfer={amount}")

    try:
        tx_hash = self.tx_id(self._transfer(_from, Ebb.get_owner(), Cent(amount)))
        get_tx_status(tx_hash)
        amount = cfg.Ebb.get_balance(_from)
        if is_verbose:
            log(f"balance_after_transfer={amount}")
    except Exception as e:
        raise e


def transfer_tokens(self, _from, to, amount):
    """Transfer tokens from the owner of the contract."""
    try:
        return self.tx_id(self._transfer(_from, to, Cent(amount)))
    except Exception as e:
        raise e


def main():
    if len(sys.argv) == 3:
        to = str(sys.argv[1])
        amount = str(sys.argv[2])
    else:
        log("E: Please provide the address and amount as argument")
        log("\t./transfer.py <address> <amount>", "info")
        sys.exit(1)

    try:
        owner_address = Ebb.get_owner()
        tx_hash = Ebb.transfer_tokens(owner_address, to, amount)
        if tx_hash:
            get_tx_status(tx_hash)
    except Exception as e:
        print_tb(e)


if __name__ == "__main__":
    main()
