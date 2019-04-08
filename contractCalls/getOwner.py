#!/usr/bin/env python3

def getOwner(eBlocBroker=None):
    if eBlocBroker is None:
        import os, sys
        sys.path.insert(1, os.path.join(sys.path[0], '..'))
        from imports import connectEblocBroker
        eBlocBroker = connectEblocBroker()

    return eBlocBroker.functions.getOwner().call()

if __name__ == '__main__': 
    print(getOwner())
