#!/usr/bin/env python

from imports import *

if __name__ == '__main__': #{
    if web3.eth.getCode(contractAddress) == '0x' or web3.eth.getCode(contractAddress) == b'':
        print('False')
    else:
        print('True')
#}
