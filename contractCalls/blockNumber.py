#!/usr/bin/env python3


def blockNumber(w3=None):
    if w3 is None:
        from imports import getWeb3
        w3 = getWeb3()
        return str(w3.eth.blockNumber).replace("\n", "")
    else:
        return str(w3.eth.blockNumber).replace("\n", "")


if __name__ == '__main__':
    print(blockNumber())
