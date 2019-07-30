#!/usr/bin/env python3

def getOwner(eBlocBroker=None):
    if eBlocBroker is None:
        import os, sys
        from imports import connectEblocBroker
        eBlocBroker = connectEblocBroker()
        if not eBlocBroker: return False
        
    return eBlocBroker.functions.getOwner().call()

if __name__ == '__main__': 
    print(getOwner())
