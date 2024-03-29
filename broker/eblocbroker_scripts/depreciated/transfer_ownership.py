#!/usr/bin/env python3

import sys

from broker import cfg
from broker._utils.tools import log, print_tb
from broker._utils.web3_tools import get_tx_status
from broker.config import env


def transfer_ownership(self, new_owner):
    """Transfer ownership."""
    _from = self.w3.toChecksumAddress(env.PROVIDER_ID)
    new_owner = self.w3.toChecksumAddress(new_owner)
    if new_owner == cfg.ZERO_ADDRESS:
        raise Exception("Provided address is zero")

    if not self.w3.isAddress(new_owner):
        raise Exception("Provided address is not valid")

    if self.is_owner(new_owner):
        raise Exception("new_owner is already the owner")

    try:
        tx = self._transfer_ownership(_from, new_owner)
        return self.tx_id(tx)
    except Exception as e:
        print_tb(e)
        raise e


if __name__ == "__main__":
    Ebb = cfg.Ebb
    if len(sys.argv) == 2:
        new_owner = str(sys.argv[1])
    else:
        log("warning: Please provide the new_owner address as argument.")
        sys.exit(1)

    try:
        tx_hash = Ebb.transfer_ownership(new_owner)
        receipt = get_tx_status(tx_hash)
    except Exception as e:
        print_tb(e)
        sys.exit(1)
