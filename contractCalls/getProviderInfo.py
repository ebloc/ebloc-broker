#!/usr/bin/env python3

import sys
from imports import connectEblocBroker, getWeb3

def getProviderInfo(provider, eBlocBroker=None, w3=None):
    if w3 is None:
        w3 = getWeb3()
        if not w3:
            return
       
    if eBlocBroker is None :
        eBlocBroker = connectEblocBroker(w3)

    provider = w3.toChecksumAddress(provider) 
    
    if str(eBlocBroker.functions.isProviderExists(provider).call()) == "False":
        print("Provider(" + provider + ") is not registered. Please try again with registered Ethereum Address as provider.")
        sys.exit() 

    providerPriceInfo = eBlocBroker.functions.getProviderInfo(provider).call()    
    blockReadFrom     = providerPriceInfo[0]    
    event_filter = eBlocBroker.events.LogProviderInfo.createFilter(fromBlock=int(blockReadFrom), toBlock=int(blockReadFrom) + 1, argument_filters={'provider': str(provider)})
    
    providerInfo = {'blockReadFrom':      blockReadFrom,
                    'availableCoreNum':   providerPriceInfo[1],
                    'priceCoreMin':       providerPriceInfo[2],
                    'priceDataTransfer':  providerPriceInfo[3],
                    'priceStorage':       providerPriceInfo[4],
                    'priceCache':         providerPriceInfo[5],
                    'commitmentBlockNum': providerPriceInfo[6],
                    'email':              event_filter.get_all_entries()[-1].args['email'],
                    'miniLockID':         event_filter.get_all_entries()[-1].args['miniLockID'],
                    'ipfsAddress':        event_filter.get_all_entries()[-1].args['ipfsAddress'],
                    'fID':                event_filter.get_all_entries()[-1].args['fID'],
                    'whisperPublicKey':   '0x' + event_filter.get_all_entries()[-1].args['whisperPublicKey']                    
    }

    return True, providerInfo


if __name__ == '__main__':
    if len(sys.argv) == 2:
        provider = str(sys.argv[1]) 
    else:        
        provider = "0x57b60037b82154ec7149142c606ba024fbb0f991"

    status, providerInfo = getProviderInfo(provider)
    
    if status:
        print('{0: <20}'.format('blockReadFrom: ')      + str(providerInfo['blockReadFrom'])      + '\n' +
              '{0: <20}'.format('availableCoreNum: ')   + str(providerInfo['availableCoreNum'])   + '\n' +
              '{0: <20}'.format('priceCoreMin: ')       + str(providerInfo['priceCoreMin'])       + '\n' +
              '{0: <20}'.format('priceDataTransfer: ')  + str(providerInfo['priceDataTransfer'])  + '\n' +
              '{0: <20}'.format('priceStorage: ')       + str(providerInfo['priceStorage'])       + '\n' +
              '{0: <20}'.format('priceCache: ')         + str(providerInfo['priceCache'])         + '\n' +               
              '{0: <20}'.format('commitmentBlockNum: ') + str(providerInfo['commitmentBlockNum']) + '\n' +              
              '{0: <20}'.format('email: ')              + providerInfo['email']                   + '\n' +  
              '{0: <20}'.format('miniLockID: ')         + providerInfo['miniLockID']              + '\n' +
              '{0: <20}'.format('ipfsAddress: ')        + providerInfo['ipfsAddress']             + '\n' +
              '{0: <20}'.format('fID: ')                + providerInfo['fID']                     + '\n' +
              '{0: <20}'.format('whisperPublicKey: ')   + providerInfo['whisperPublicKey']
        )
