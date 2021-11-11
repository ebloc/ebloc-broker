#!/usr/bin/env python3

"""Authenticate orc_id."""

import sys
from typing import Union

from broker import cfg
from broker._utils.tools import log, print_tb
from broker.lib import get_tx_status


def authenticate_orc_id(self, address, orc_id, _from) -> Union[None, str]:
    """Authenticate orc_id."""
    address = self.w3.toChecksumAddress(address)
    if not self.w3.isAddress(_from):
        log(f"E: Account: {_from} is not a valid address")
        raise

    if not self.is_owner(_from):
        breakpoint()  # DEBUG
        log(f"E: Account: {_from} that will call the transaction is not the owner of the contract")
        raise

    output = self.does_provider_exist(address)
    if not self.does_requester_exist(address) and not output:
        log(f"E: Address: {address} is not registered")
        raise

    if len(orc_id) != 19:
        log("E: orc_id length is not 19")
        raise

    if not orc_id.replace("-", "").isdigit():
        log("E: orc_id contains characters")
        raise

    if not self._is_orc_id_verified(address):
        try:
            tx = self._authenticate_orc_id(_from, address, str.encode(orc_id))
            return self.tx_id(tx)
        except Exception as e:
            raise e
    else:
        log(f"## Address: {address} that has orc_id: {orc_id} is already authenticated")
        return None


if __name__ == "__main__":
    Ebb = cfg.Ebb
    if len(sys.argv) == 3:
        address = str(sys.argv[1])
        orc_id = str(sys.argv[2])
    else:
        log("E: Please provide the address and its orc_id as argument.\n./authenticate_orc_id.py <address> <orc_id>")
        sys.exit(1)
        """
        ./authenticate_orc_id.py 0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49 0000-0001-7642-0552  # home-1
        """
    try:
        owner_address = Ebb.get_owner()
        tx_hash = Ebb.authenticate_orc_id(address, orc_id, owner_address)
        if tx_hash:
            receipt = get_tx_status(tx_hash)
    except Exception as e:
        print_tb(e)
