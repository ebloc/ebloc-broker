#!/usr/bin/env python3

import sys
import traceback

from config import load_log
from doesProviderExist import doesProviderExist
from doesRequesterExist import doesRequesterExist
from imports import connect
from is_owner import is_owner
from lib import get_tx_status


def authenticateORCID(address, orc_id) -> (bool, str):
    eBlocBroker, w3 = connect()
    if eBlocBroker is None or w3 is None:
        return

    account = w3.eth.accounts[0]
    address = w3.toChecksumAddress(address)

    if not w3.isAddress(account):
        return False, f"E: Account: {account} is not a valid address."

    if not is_owner(account):
        return (False, f"E: Account: {account} that will call the transaction is not the owner of the contract.")

    output = doesProviderExist(address)
    if not doesRequesterExist(address) and not output:
        return False, f"E: Address: {address} is not registered."

    if len(orc_id) != 19:
        return False, "E: orc_id length is not 19."

    if not orc_id.replace("-", "").isdigit():
        return False, "E: orc_id contains characters."

    if not eBlocBroker.functions.isOrcIDVerified(address).call():
        try:
            tx = eBlocBroker.functions.authenticateOrcID(address, str.encode(orc_id)).transact({"from": account, "gas": 4500000})
        except Exception:
            return False, traceback.format_exc()
        return True, tx.hex()
    else:
        return (False, f"address: {address} that has orc_id: {orc_id} is already authenticated.")


if __name__ == "__main__":
    global logging
    logging = load_log()

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

    success, output = authenticateORCID(address, orc_id)
    if success:
        receipt = get_tx_status(success, output)
    else:
        logging.error(output)
