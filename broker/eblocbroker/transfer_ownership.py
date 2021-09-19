#!/usr/bin/env python3

import sys

from broker._utils.tools import _colorize_traceback, log
from broker.config import env
from broker.lib import get_tx_status
from broker.utils import ZERO_ADDRESS


def transfer_ownership(self, new_owner):
    """Transfer ownership."""
    _from = self.w3.toChecksumAddress(env.PROVIDER_ID)
    new_owner = self.w3.toChecksumAddress(new_owner)
    if new_owner == ZERO_ADDRESS:
        raise Exception("E: Provided address is zero")

    if not self.w3.isAddress(new_owner):
        raise Exception("E: Provided address is not valid")

    if self.is_owner(new_owner):
        raise Exception("E: new_owner is already the owner")

    try:
        tx = self._transfer_ownership(_from, new_owner)
        return self.tx_id(tx)
    except Exception as e:
        _colorize_traceback(e)
        raise e


if __name__ == "__main__":
    import broker.eblocbroker.Contract as Contract

    Ebb = Contract.ebb()
    if len(sys.argv) == 2:
        new_owner = str(sys.argv[1])
    else:
        log("Warning: Please provide the new_owner address as argument.")
        sys.exit(1)

    try:
        tx_hash = Ebb.transfer_ownership(new_owner)
        receipt = get_tx_status(tx_hash)
    except Exception as e:
        _colorize_traceback(e)
        sys.exit(1)
