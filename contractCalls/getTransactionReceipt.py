#!/usr/bin/env python3

import os, sys

"""
doc: https://web3py.readthedocs.io/en/stable/web3.eth.html#web3.eth.Eth.getTransactionReceipt
Returns the transaction receipt specified by transaction_hash. 
If the transaction has not yet been mined returns 'None'
"""


def getTransactionReceipt(tx, w3=None):
    if w3 is None:
        from imports import getWeb3

        w3 = getWeb3()

    return True, w3.eth.getTransactionReceipt(tx)


if __name__ == "__main__":
    if len(sys.argv) == 2:
        tx = str(sys.argv[1])
    else:
        tx = "0xfa65c8516e81f972d1bdf801e0524aad1b2a9c54bb8e746613fb7316034f3e3e"

    status, result = getTransactionReceipt(tx)
    print(result)
    # print(getTransactionReceipt(tx)['blockNumber'])
