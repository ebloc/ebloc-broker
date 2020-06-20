#!/usr/bin/env python3

import sys

import config
from config import logging
from lib import get_tx_status
from utils import _colorize_traceback


def authenticate_orc_id(self, address, orc_id, _from) -> (bool, str):
    address = self.w3.toChecksumAddress(address)

    if not self.w3.isAddress(_from):
        logging.error(f"E: Account: {_from} is not a valid address")
        raise

    if not self.is_owner(_from):
        logging.error(f"E: Account: {_from} that will call the transaction is not the owner of the contract",)
        raise

    output = self.does_provider_exist(address)
    if not self.does_requester_exist(address) and not output:
        logging.error(f"E: Address: {address} is not registered")
        raise

    if len(orc_id) != 19:
        logging.error("E: orc_id length is not 19")
        raise

    if not orc_id.replace("-", "").isdigit():
        logging.error("E: orc_id contains characters")
        raise

    if not self.eBlocBroker.functions.isOrcIDVerified(address).call():
        try:
            tx = self.eBlocBroker.functions.authenticateOrcID(address, str.encode(orc_id)).transact(
                {"from": _from, "gas": 4500000}
            )
            return tx.hex()
        except Exception:
            logging.error(_colorize_traceback)
            raise
    else:
        logging.warning(f"\nAddress: {address} that has orc_id: {orc_id} is already authenticated")
        return None


if __name__ == "__main__":
    import eblocbroker.Contract as Contract

    Ebb = Contract.eblocbroker

    if len(sys.argv) == 3:
        address = str(sys.argv[1])
        orc_id = str(sys.argv[2])
    else:
        logging.error("E: Please provide the address and its orc_id as argument.")
        sys.exit(1)
        # ./authenticate_orc_id.py 0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49 0000-0001-7642-0552
        # 0x12ba09353d5C8aF8Cb362d6FF1D782C1E195b571 # home / requester
        # address = '0x57b60037b82154ec7149142c606ba024fbb0f991' # netlab
        # address = '0x90Eb5E1ADEe3816c85902FA50a240341Fa7d90f5' # prc
        # orc_id       = '0000-0001-7642-0552'

    try:
        tx_hash = Ebb.authenticate_orc_id(address, orc_id, _from=config.w3.eth.accounts[0])
        if tx_hash:
            receipt = get_tx_status(tx_hash)
    except:
        _colorize_traceback()
