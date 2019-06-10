#!/usr/bin/env python3

import sys, os

def getClusterAddresses(eBlocBroker=None):
    if eBlocBroker is None: 
        from imports import connectEblocBroker
        eBlocBroker = connectEblocBroker()

    if eBlocBroker == 'notconnected':
        return eBlocBroker
    return eBlocBroker.functions.getClusterAddresses().call(), eBlocBroker

def getClusterPriceInfo(clusterAddress, requestedCore, coreMinuteGas, gasDataTransfer):
    blockReadFrom, coreNumber, priceCoreMin, priceDataTransfer = eBlocBroker.functions.getClusterInfo(clusterAddress).call()
        
    print('{0: <19}'.format('coreNumber: ')        + str(coreNumber))
    print('{0: <19}'.format('priceCoreMin: ')      + str(priceCoreMin))
    print('{0: <19}'.format('priceDataTransfer: ') + str(priceDataTransfer))
    if requestedCore > coreNumber:
        print('{0: <19}'.format('price: ') + 'Requested core is greater than cluster\'s core')
    else:
        print('{0: <19}'.format('price: ') + str(requestedCore * coreMinuteGas * priceCoreMin + gasDataTransfer * priceDataTransfer))

if __name__ == '__main__':
    clusterList, eBlocBroker = getClusterAddresses()
    if clusterList == 'notconnected':
        print(clusterList)
        sys.exit()
        
    requestedCore   = 2
    coreGasDay      = 0
    coreGasHour     = 0
    coreGasMin      = 1
    coreMinuteGas   = coreGasMin + coreGasHour * 60 + coreGasDay * 1440   
    dataTransferIn  = 100
    dataTransferOut = 100
    gasDataTransfer  = dataTransferIn + dataTransferOut
        
    for i in range(0, len(clusterList)):
        print(clusterList[i])
        getClusterPriceInfo(clusterList[i], requestedCore, coreMinuteGas, gasDataTransfer)
              
        if i != len(clusterList) -1:
            print('')
