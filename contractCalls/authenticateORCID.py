#!/usr/bin/env python3

import sys

from config import logging
from does_requester_exist import does_requester_exist
from doesProviderExist import doesProviderExist
from imports import connect
from is_owner import is_owner
from lib import get_tx_status
from utils import _colorize_traceback


def authenticateORCID(address, orc_id) -> (bool, str):
    eBlocBroker, w3 = connect()

    account = w3.eth.accounts[0]
    address = w3.toChecksumAddress(address)

    if not w3.isAddress(account):
        logging.error(f"E: Account: {account} is not a valid address.")
        raise

    if not is_owner(account):
        logging.error(f"E: Account: {account} that will call the transaction is not the owner of the contract.",)
        raise

    output = doesProviderExist(address)
    if not does_requester_exist(address) and not output:
        logging.error(f"E: Address: {address} is not registered.")
        raise

    if len(orc_id) != 19:
        logging.error("E: orc_id length is not 19.")
        raise

    if not orc_id.replace("-", "").isdigit():
        logging.error("E: orc_id contains characters.")
        raise

    if not eBlocBroker.functions.isOrcIDVerified(address).call():
        try:
            tx = eBlocBroker.functions.authenticateOrcID(address, str.encode(orc_id)).transact(
                {"from": account, "gas": 4500000}
            )
            return tx.hex()
        except Exception:
            logging.error(_colorize_traceback)
            raise
    else:
        logging.warning(f"Address: {address} that has orc_id: {orc_id} is already authenticated")
        return None


if __name__ == "__main__":
    if len(sys.argv) == 3:
        address = str(sys.argv[1])
        orc_id = str(sys.argv[2])
    else:
        logging.error("E: Please provide the address and its orc_id as argument.")
        sys.exit(1)
        # ./authenticateORCID.py 0x57b60037b82154ec7149142c606ba024fbb0f991 0000-0001-7642-0552
        # address = '0x57b60037b82154ec7149142c606ba024fbb0f991' # netlab
        # address = '0x90Eb5E1ADEe3816c85902FA50a240341Fa7d90f5' # prc
        # orc_id       = '0000-0001-7642-0552'

    try:
        tx_hash = authenticateORCID(address, orc_id)
        if tx_hash:
            receipt = get_tx_status(tx_hash)
    except:
        print(_colorize_traceback())
