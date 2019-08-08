#!/usr/bin/env python3

import sys 

def getProviderReceivedAmount(providerAddress, eBlocBroker=None, web3=None):
    if eBlocBroker is not None and web3 is not None:
        providerAddress = web3.toChecksumAddress(providerAddress)         
        return str(eBlocBroker.functions.getProviderReceivedAmount(providerAddress).call()).rstrip('\n') 
    else:
        import os         
        from imports import connectEblocBroker, getWeb3
        
        web3 = getWeb3() 
        providerAddress = web3.toChecksumAddress(providerAddress)                
        eBlocBroker    = connectEblocBroker(web3)
        return str(eBlocBroker.functions.getProviderReceivedAmount(providerAddress).call()).rstrip('\n') 
    
if __name__ == '__main__':
    if len(sys.argv) == 2:
        providerAddress = str(sys.argv[1])
        print(getProviderReceivedAmount(providerAddress))
    else:
        print('Please provide provider address as argument.')          
