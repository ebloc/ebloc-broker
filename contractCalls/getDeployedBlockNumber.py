#!/usr/bin/env python3

import sys 

def getDeployedBlockNumber(eBlocBroker=None):
    if eBlocBroker is None: 
        import os 
        from imports import connectEblocBroker        
        eBlocBroker = connectEblocBroker() 

    return eBlocBroker.functions.getDeployedBlockNumber().call() 

if __name__ == '__main__':
    print(getDeployedBlockNumber())
    
