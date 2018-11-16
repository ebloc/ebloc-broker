#!/usr/bin/env python3

import sys

def getClusterInfo(clusterAddress, eBlocBroker=None, web3=None): 
    if eBlocBroker == None and web3 == None: 
        import os
        sys.path.insert(1, os.path.join(sys.path[0], '..'))
        from imports import connectEblocBroker
        from imports import getWeb3
        web3        = getWeb3()
        eBlocBroker = connectEblocBroker(web3)

    clusterAddress = web3.toChecksumAddress(clusterAddress) 
    
    if str(eBlocBroker.functions.isClusterExist(clusterAddress).call()) == "False":
        print("Cluster is not registered. Please try again with registered Ethereum Address as cluster.")
        sys.exit() 

    blockReadFrom, coreNumber, priceCoreMin, priceBandwidthMB = eBlocBroker.functions.getClusterInfo(clusterAddress).call() 
    my_filter = eBlocBroker.eventFilter('LogCluster',{'fromBlock': int(blockReadFrom),'toBlock': int(blockReadFrom) + 1})

    return('{0: <18}'.format('blockReadFrom: ')    + str(blockReadFrom)  + '\n' +
           '{0: <18}'.format('coreNumber: ')       + str(coreNumber) + '\n' +
           '{0: <18}'.format('priceCoreMin: ')     + str(priceCoreMin)  + '\n' +
           '{0: <18}'.format('priceBandwidthMB: ') + str(priceBandwidthMB)  + '\n' +           
           '{0: <18}'.format('clusterEmail: ')     + my_filter.get_all_entries()[0].args['clusterEmail'] + '\n' +
           '{0: <18}'.format('miniLockID: ')       + my_filter.get_all_entries()[0].args['miniLockID'] + '\n' +
           '{0: <18}'.format('ipfsAddress: ')      + my_filter.get_all_entries()[0].args['ipfsAddress'] + '\n' +
           '{0: <18}'.format('fID: ')              + my_filter.get_all_entries()[0].args['fID'] + '\n' +
           '{0: <18}'.format('whisperPublicKey: ') + my_filter.get_all_entries()[0].args['whisperPublicKey']);

if __name__ == '__main__':
    if len(sys.argv) == 2:
        clusterAddress = str(sys.argv[1]) 
    else:        
        clusterAddress = "0x4e4a0750350796164D8DefC442a712B7557BF282"  #POA
        # clusterAddress = "0x6af0204187a93710317542d383a1b547fa42e705"  #POW
    print(getClusterInfo(clusterAddress))
