#!/usr/bin/env python

import sys 

def getClusterReceivedAmount(clusterAddress, eBlocBroker=None, web3=None): #{
    if eBlocBroker != None and web3 != None:
        clusterAddress = web3.toChecksumAddress(clusterAddress)         
        return str(eBlocBroker.functions.getClusterReceivedAmount(clusterAddress).call()).rstrip('\n') 
    else:
        import os         
        sys.path.insert(1, os.path.join(sys.path[0], '..')) 
        from imports import connectEblocBroker
        from imports import getWeb3
        
        web3 = getWeb3() 
        clusterAddress = web3.toChecksumAddress(clusterAddress)                
        eBlocBroker    = connectEblocBroker(web3)
        return str(eBlocBroker.functions.getClusterReceivedAmount(clusterAddress).call()).rstrip('\n') 
#}
    
if __name__ == '__main__': #{
    if len(sys.argv) == 2:
        clusterAddress = str(sys.argv[1])  # ex: 0x4e4a0750350796164d8defc442a712b7557bf282
        print(getClusterReceivedAmount(clusterAddress))
    else:
        print('Please provide cluster address as argument.')          
#}
