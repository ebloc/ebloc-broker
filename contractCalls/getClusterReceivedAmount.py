#!/usr/bin/env python3

import sys 

def getClusterReceivedAmount(clusterAddress, eBlocBroker=None, web3=None):
    if eBlocBroker is not None and web3 is not None:
        clusterAddress = web3.toChecksumAddress(clusterAddress)         
        return str(eBlocBroker.functions.getClusterReceivedAmount(clusterAddress).call()).rstrip('\n') 
    else:
        import os         
        from imports import connectEblocBroker, getWeb3
        
        web3 = getWeb3() 
        clusterAddress = web3.toChecksumAddress(clusterAddress)                
        eBlocBroker    = connectEblocBroker(web3)
        return str(eBlocBroker.functions.getClusterReceivedAmount(clusterAddress).call()).rstrip('\n') 
    
if __name__ == '__main__':
    if len(sys.argv) == 2:
        clusterAddress = str(sys.argv[1])
        print(getClusterReceivedAmount(clusterAddress))
    else:
        print('Please provide cluster address as argument.')          
