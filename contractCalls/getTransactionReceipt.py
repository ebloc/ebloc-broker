#!/usr/bin/env python3

import os, sys

'''
doc: https://web3py.readthedocs.io/en/stable/web3.eth.html#web3.eth.Eth.getTransactionReceipt
Returns the transaction receipt specified by transaction_hash. 
If the transaction has not yet been mined returns 'None'
'''

def getTransactionReceipt(tx, web3=None):
    if web3 is None: 
        sys.path.insert(1, os.path.join(sys.path[0], '..'))
        from imports import getWeb3
        web3 = getWeb3()

    return web3.eth.getTransactionReceipt(tx)

if __name__ == '__main__':
    if len(sys.argv) == 2:
        tx = str(sys.argv[1])
    else:
        tx = "0xfa65c8516e81f972d1bdf801e0524aad1b2a9c54bb8e746613fb7316034f3e3e"

    print(getTransactionReceipt(tx))
    #print(getTransactionReceipt(tx)['blockNumber'])    
