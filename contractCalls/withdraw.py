#!/usr/bin/env python3

import pprint
import sys
import traceback

from imports import connect, connect_to_eblocbroker, connect_to_web3


def withdraw(account):
    eBlocBroker, w3 = connect()
    account = w3.toChecksumAddress(account)
    try:
        tx = eBlocBroker.functions.withdraw().transact({"from": account, "gas": 50000})
    except Exception:
        return False, traceback.format_exc()

    return True, tx.hex()


if __name__ == "__main__":
    w3 = connect_to_web3()
    eBlocBroker = connect_to_eblocbroker(w3)

    if len(sys.argv) == 2:
        account = str(sys.argv[1])
    else:
        print("Please provide an Ethereum account as an argument.")
        sys.exit()

    status, result = withdraw(account)
    if status:
        print(f"tx_hash={result}")
        receipt = w3.eth.waitForTransactionReceipt(result)
        print("Transaction receipt mined: \n")
        pprint.pprint(dict(receipt))
        print("Was transaction successful?")
        pprint.pprint(receipt["status"])
    else:
        print(result)
