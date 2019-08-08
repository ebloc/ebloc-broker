#!/usr/bin/env python3

import sys

def isAddress(addr, web3=None):
    if web3 is None:
        import os
        from imports import getWeb3
        web3 = getWeb3()

    if web3 == 'notconnected':
        return web3
    
    return web3.isAddress(addr)

if __name__ == '__main__':
    if len(sys.argv) == 2:
        provider = str(sys.argv[1]) 
    else:        
        provider = '0x4e4a0750350796164D8DefC442a712B7557BF282'
    print(isAddress(provider))
