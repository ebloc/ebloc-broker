#!/usr/bin/env python3

import sys

from imports import connect_to_web3
from utils import _colorize_traceback


def getTransactionReceipt(tx):
    """
    doc: https://web3py.readthedocs.io/en/stable/web3.eth.html#web3.eth.Eth.getTransactionReceipt
    Returns the transaction receipt specified by transactionHash.
    If the transaction has not yet been mined returns 'None'
    """
    w3 = connect_to_web3()
    return w3.eth.getTransactionReceipt(tx)


if __name__ == "__main__":
    if len(sys.argv) == 2:
        tx = str(sys.argv[1])
    else:
        tx = "0xfa65c8516e81f972d1bdf801e0524aad1b2a9c54bb8e746613fb7316034f3e3e"

    try:
        print(getTransactionReceipt(tx))
        # print(getTransactionReceipt(tx)['blockNumber'])
    except:
        print(_colorize_traceback())
        sys.exit(1)
