#!/usr/bin/env python3

"""Authenticate orc_id."""

import sys
from typing import Union

from broker import cfg
from broker._utils.tools import log, print_tb
from broker._utils.web3_tools import get_tx_status


def authenticate_orc_id(self, address, orc_id, _from) -> Union[None, str]:
    """Authenticate orc_id.

    cmd: ./authenticate_orc_id.py 0x29e613B04125c16db3f3613563bFdd0BA24Cb629 0000-0001-7642-0552
    """
    address = self.w3.toChecksumAddress(address)
    log(f"## authenticating user={address}")
    if not self.w3.isAddress(_from):
        raise Exception(f"Account: {_from} is not a valid address")

    if not self.is_owner(_from):
        breakpoint()  # DEBUG
        raise Exception(f"Account: {_from} that will call the transaction is not the owner of the contract")

    if not self.does_requester_exist(address) and not self.does_provider_exist(address):
        raise Exception(f"Address: {address} is not registered")

    if len(orc_id) != 19:
        raise Exception("orc_id length is not 19")

    if not orc_id.replace("-", "").isdigit():
        raise Exception("orc_id contains characters")

    if self._is_orc_id_verified(address):
        raise Exception(f"## Address: {address} that has orc_id: {orc_id} is already authenticated")

    try:
        tx = self._authenticate_orc_id(_from, address, str.encode(orc_id))
        return self.tx_id(tx)
    except Exception as e:
        raise e


def main():
    Ebb = cfg.Ebb
    if len(sys.argv) == 3:
        address = str(sys.argv[1])
        orc_id = str(sys.argv[2])
    else:
        log("E: Please provide the address and its orc_id as argument")
        log("[bold]   ./authenticate_orc_id.py <address> <orc_id>", "mangenta")
        sys.exit(1)

    try:
        owner_address = Ebb.get_owner()
        tx_hash = Ebb.authenticate_orc_id(address, orc_id, owner_address)
        if tx_hash:
            get_tx_status(tx_hash)
    except Exception as e:
        print_tb(e)


if __name__ == "__main__":
    main()
