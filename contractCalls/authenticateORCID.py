#!/usr/bin/env python3

import sys
import traceback
import pprint

from doesRequesterExist import doesRequesterExist
from doesProviderExist import doesProviderExist

from imports import connect, connectEblocBroker, getWeb3
from is_owner import is_owner


def authenticateORCID(address, orcID, eBlocBroker=None, w3=None):
    eBlocBroker, w3 = connect(eBlocBroker, w3)
    if eBlocBroker is None or w3 is None:
        return

    account = w3.eth.accounts[0]
    address = w3.toChecksumAddress(address)

    if not w3.isAddress(account):
        return False, "Account: " + account + " is not a valid address."

    if not is_owner(account):
        return (False, "Account: " + account + " that will call the transaction is not the owner of the contract.")

    if not doesRequesterExist(address) and not doesProviderExist(address):
        return False, "address: " + address + " is not registered."

    if len(orcID) != 19:
        return False, "orcID length is not 19."

    if not orcID.replace("-", "").isdigit():
        return False, "orcID contains characters."

    if eBlocBroker.functions.isOrcIDVerified(address).call() == 0:
        try:
            tx = eBlocBroker.functions.authenticateOrcID(address, str.encode(orcID)).transact(
                {"from": account, "gas": 4500000}
            )
        except Exception:
            return False, traceback.format_exc()

        return True, tx.hex()
    else:
        return (False, "address: " + address + " that has OrcID: " + orcID + " is already authenticated.")


if __name__ == "__main__":
    w3 = getWeb3()
    eBlocBroker = connectEblocBroker(w3)

    if len(sys.argv) == 3:
        address = str(sys.argv[1])
        orcID = str(sys.argv[2])
    else:
        print("Please provide the address and its orcID as argument.")
        sys.exit()
        # ./authenticateORCID.py 0x57b60037b82154ec7149142c606ba024fbb0f991 0000-0001-7642-0552
        # address = '0x57b60037b82154ec7149142c606ba024fbb0f991' # netlab
        # address = '0x90Eb5E1ADEe3816c85902FA50a240341Fa7d90f5' # prc
        # orcID       = '0000-0001-7642-0552'

    status, result = authenticateORCID(address, orcID, eBlocBroker, w3)
    if status:
        print("tx_hash=" + result)
        receipt = w3.eth.waitForTransactionReceipt(result)
        print("Transaction receipt mined: \n")
        pprint.pprint(dict(receipt))
        print("Was transaction successful?")
        pprint.pprint(receipt["status"])
    else:
        print(result)
