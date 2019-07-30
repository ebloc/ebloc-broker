#!/usr/bin/env python3

import sys

def getClusterInfo(clusterAddress, eBlocBroker=None, web3=None): 
    if eBlocBroker is None and web3 is None: 
        import os
        from imports import connectEblocBroker, getWeb3
        web3        = getWeb3()
        eBlocBroker = connectEblocBroker(web3)

    clusterAddress = web3.toChecksumAddress(clusterAddress) 
    
    if str(eBlocBroker.functions.isClusterExist(clusterAddress).call()) == "False":
        print("Cluster(" + clusterAddress + ") is not registered. Please try again with registered Ethereum Address as cluster.")
        sys.exit() 

    clusterPriceInfo = eBlocBroker.functions.getClusterInfo(clusterAddress).call()
    blockReadFrom      = clusterPriceInfo[0]
    availableCoreNum   = clusterPriceInfo[1]    
    priceCoreMin       = clusterPriceInfo[2]
    priceDataTransfer  = clusterPriceInfo[3]
    priceStorage       = clusterPriceInfo[4]
    priceCache         = clusterPriceInfo[5]
    commitmentBlockNum = clusterPriceInfo[6]

    my_filter = eBlocBroker.eventFilter('LogClusterInfo', {'fromBlock': int(blockReadFrom) - 100, 'toBlock': int(blockReadFrom) + 1})
    '''
    my_filter = eBlocBroker.events.LogCluster.createFilter(
        fromBlock=int(blockReadFrom),       
        toBlock=int(blockReadFrom) + 1,
        argument_filters={'clusterAddress': str(clusterAddress)}
    )    
    loggedJobs = my_filter.get_all_entries()
    print(loggedJobs[0])
    sp'''
    # print(my_filter.get_all_entries()[0])
    
    return('{0: <20}'.format('blockReadFrom: ')     + str(blockReadFrom)  + '\n' +
           '{0: <20}'.format('availableCoreNum: ')  + str(availableCoreNum) + '\n' +
           '{0: <20}'.format('priceCoreMin: ')      + str(priceCoreMin)  + '\n' +
           '{0: <20}'.format('priceDataTransfer: ') + str(priceDataTransfer)  + '\n' +
           '{0: <20}'.format('priceStorage: ')      + str(priceStorage)  + '\n' +
           '{0: <20}'.format('priceCache: ')        + str(priceCache)  + '\n' +
           '{0: <20}'.format('commitmentBlockNum: ')  + str(commitmentBlockNum) + '\n' +
           '{0: <20}'.format('clusterEmail: ')      + my_filter.get_all_entries()[0].args['clusterEmail'] + '\n' +
           '{0: <20}'.format('miniLockID: ')        + my_filter.get_all_entries()[0].args['miniLockID'] + '\n' +
           '{0: <20}'.format('ipfsAddress: ')       + my_filter.get_all_entries()[0].args['ipfsAddress'] + '\n' +
           '{0: <20}'.format('fID: ')               + my_filter.get_all_entries()[0].args['fID'] + '\n' +
           '{0: <20}'.format('whisperPublicKey: ')  + '0x' + my_filter.get_all_entries()[0].args['whisperPublicKey']);

if __name__ == '__main__':
    if len(sys.argv) == 2:
        clusterAddress = str(sys.argv[1]) 
    else:        
        clusterAddress = "0x4e4a0750350796164D8DefC442a712B7557BF282"

    print(getClusterInfo(clusterAddress))
