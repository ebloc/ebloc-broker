#!/usr/bin/env python3

import sys

from config import env, logging
from lib import get_tx_status
from utils import _colorize_traceback


def transfer_ownership(self, new_owner):
    _from = self.w3.toChecksumAddress(env.PROVIDER_ID)
    new_owner = self.w3.toChecksumAddress(new_owner)
    if new_owner == "0x0000000000000000000000000000000000000000":
        logging.error("Provided address is zero")
        raise

    if not self.w3.isAddress(new_owner):
        logging.error("Provided address is not valid")
        raise

    if self.eBlocBroker.functions.getOwner().call() == new_owner:
        logging.error("new_owner is already the owner")
        raise

    try:
        tx = self.eBlocBroker.functions.transferOwnership(new_owner).transact({"from": _from, "gas": 4500000})
        return tx.hex()
    except Exception:
        _colorize_traceback()
        raise


if __name__ == "__main__":
    import eblocbroker.Contract as Contract

    ebb = Contract.eblocbroker

    if len(sys.argv) == 2:
        new_owner = str(sys.argv[1])
    else:
        print("Please provide the new_owner address as argument.")
        sys.exit(1)

    try:
        tx_hash = ebb.transfer_ownership(new_owner)
        receipt = get_tx_status(tx_hash)
    except:
        _colorize_traceback()
        sys.exit(1)
