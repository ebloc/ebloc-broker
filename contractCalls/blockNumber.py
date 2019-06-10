#!/usr/bin/env python3

def blockNumber(web3=None):
    if web3 is None:
        import sys, os
        from imports import getWeb3
        web3 = getWeb3()
        return str(web3.eth.blockNumber).replace("\n", "")
    else:
        return str(web3.eth.blockNumber).replace("\n", "")

if __name__ == '__main__':
    print(blockNumber())
