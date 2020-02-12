#!/usr/bin/env python3

import pprint
import sys
import traceback

from doesProviderExist import doesProviderExist
from doesRequesterExist import doesRequesterExist
from imports import connect, connect_to_eblocbroker, connect_to_web3
from is_owner import is_owner


def authenticateORCID(address, orc_id):
    eBlocBroker, w3 = connect()
    if eBlocBroker is None or w3 is None:
        return

    account = w3.eth.accounts[0]
    address = w3.toChecksumAddress(address)

    if not w3.isAddress(account):
        return False, f"Account: {account} is not a valid address."

    if not is_owner(account):
        return (False, f"Account: {account} that will call the transaction is not the owner of the contract.")

    status, result = doesProviderExist(address)
    if not doesRequesterExist(address) and not result:
        return False, f"address: {address} is not registered."

    if len(orc_id) != 19:
        return False, "orc_id length is not 19."

    if not orc_id.replace("-", "").isdigit():
        return False, "orc_id contains characters."

    if eBlocBroker.functions.isOrcIDVerified(address).call() == 0:
        try:
            tx = eBlocBroker.functions.authenticateOrcID(address, str.encode(orc_id)).transact(
                {"from": account, "gas": 4500000}
            )
        except Exception:
            return False, traceback.format_exc()

        return True, tx.hex()
    else:
        return (False, f"address: {address} that has orc_id: {orc_id} is already authenticated.")


if __name__ == "__main__":
    w3 = connect_to_web3()
    eBlocBroker = connect_to_eblocbroker(w3)

    if len(sys.argv) == 3:
        address = str(sys.argv[1])
        orc_id = str(sys.argv[2])
    else:
        print("Please provide the address and its orc_id as argument.")
        sys.exit()
        # ./authenticateORCID.py 0x57b60037b82154ec7149142c606ba024fbb0f991 0000-0001-7642-0552
        # address = '0x57b60037b82154ec7149142c606ba024fbb0f991' # netlab
        # address = '0x90Eb5E1ADEe3816c85902FA50a240341Fa7d90f5' # prc
        # orc_id       = '0000-0001-7642-0552'

    status, result = authenticateORCID(address, orc_id)
    if status:
        print("tx_hash=" + result)
        receipt = w3.eth.waitForTransactionReceipt(result)
        print("Transaction receipt mined: \n")
        pprint.pprint(dict(receipt))
        print("Was transaction successful?")
        pprint.pprint(receipt["status"])
    else:
        print(result)
