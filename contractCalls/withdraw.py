#!/usr/bin/env python3

import sys
import pprint
from imports import connect, connectEblocBroker, getWeb3


def withdraw(account, eBlocBroker=None, web3=None):
    eBlocBroker, w3 = connect(eBlocBroker, web3)
    if eBlocBroker is None or w3 is None:
        return
    account = web3.toChecksumAddress(account)
    try:
        tx = eBlocBroker.functions.withdraw().transact({"from": account, "gas": 30000})
    except Exception:
        return False, traceback.format_exc()

    return True, tx.hex()


if __name__ == '__main__':
    w3 = getWeb3()
    eBlocBroker = connectEblocBroker(w3)

    if len(sys.argv) == 2:
        account = str(sys.argv[1])
    else:
        print('Please provide an Ethereum account as an argument.')
        sys.exit()

    status, result = withdraw(account, eBlocBroker, w3)
    if status:
        print('tx_hash=' + result)
        receipt = w3.eth.waitForTransactionReceipt(result)
        print("Transaction receipt mined: \n")
        pprint.pprint(dict(receipt))
        print("Was transaction successful?")
        pprint.pprint(receipt['status'])
    else:
        print(result)
