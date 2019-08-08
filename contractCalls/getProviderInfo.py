#!/usr/bin/env python3

import sys

def getProviderInfo(providerAddress, eBlocBroker=None, web3=None): 
    if eBlocBroker is None and web3 is None: 
        import os
        from imports import connectEblocBroker, getWeb3
        web3        = getWeb3()
        eBlocBroker = connectEblocBroker(web3)

    providerAddress = web3.toChecksumAddress(providerAddress) 
    
    if str(eBlocBroker.functions.isProviderExists(providerAddress).call()) == "False":
        print("Provider(" + providerAddress + ") is not registered. Please try again with registered Ethereum Address as provider.")
        sys.exit() 

    providerPriceInfo  = eBlocBroker.functions.getProviderInfo(providerAddress).call()
    blockReadFrom      = providerPriceInfo[0]
    availableCoreNum   = providerPriceInfo[1]    
    priceCoreMin       = providerPriceInfo[2]
    priceDataTransfer  = providerPriceInfo[3]
    priceStorage       = providerPriceInfo[4]
    priceCache         = providerPriceInfo[5]
    commitmentBlockNum = providerPriceInfo[6]

    my_filter = eBlocBroker.eventFilter('LogProviderInfo', {'fromBlock': int(blockReadFrom) - 100, 'toBlock': int(blockReadFrom) + 1})
    '''
    my_filter = eBlocBroker.events.LogProvider.createFilter(
        fromBlock=int(blockReadFrom),       
        toBlock=int(blockReadFrom) + 1,
        argument_filters={'providerAddress': str(providerAddress)}
    )    
    loggedJobs = my_filter.get_all_entries()
    print(loggedJobs[0])
    sp'''
    # print(my_filter.get_all_entries()[0])
    
    return('{0: <20}'.format('blockReadFrom: ')      + str(blockReadFrom)  + '\n' +
           '{0: <20}'.format('availableCoreNum: ')   + str(availableCoreNum) + '\n' +
           '{0: <20}'.format('priceCoreMin: ')       + str(priceCoreMin)  + '\n' +
           '{0: <20}'.format('priceDataTransfer: ')  + str(priceDataTransfer)  + '\n' +
           '{0: <20}'.format('priceStorage: ')       + str(priceStorage)  + '\n' +
           '{0: <20}'.format('priceCache: ')         + str(priceCache)  + '\n' +
           '{0: <20}'.format('commitmentBlockNum: ') + str(commitmentBlockNum) + '\n' +
           '{0: <20}'.format('email: ')              + my_filter.get_all_entries()[0].args['email'] + '\n' +
           '{0: <20}'.format('miniLockID: ')         + my_filter.get_all_entries()[0].args['miniLockID'] + '\n' +
           '{0: <20}'.format('ipfsAddress: ')        + my_filter.get_all_entries()[0].args['ipfsAddress'] + '\n' +
           '{0: <20}'.format('fID: ')                + my_filter.get_all_entries()[0].args['fID'] + '\n' +
           '{0: <20}'.format('whisperPublicKey: ')   + '0x' + my_filter.get_all_entries()[0].args['whisperPublicKey']);

if __name__ == '__main__':
    if len(sys.argv) == 2:
        providerAddress = str(sys.argv[1]) 
    else:        
        providerAddress = "0x57b60037b82154ec7149142c606ba024fbb0f991"

    print(getProviderInfo(providerAddress))
