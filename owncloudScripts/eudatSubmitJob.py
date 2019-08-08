#!/usr/bin/env python3

import os, owncloud, subprocess, sys, time
# sys.path.insert(1, os.path.join(sys.path[0], '..'))
import lib
from imports import connectEblocBroker, getWeb3

web3        = getWeb3()
eBlocBroker = connectEblocBroker(web3)

from contractCalls.submitJob import submitJob
from isOcMounted             import isOcMounted

from lib_owncloud import singleFolderShare
from lib_owncloud import eudatInitializeFolder
from lib_owncloud import isOcMounted

def eudatSubmitJob(oc, tarHash=None): # fc33e7908fdf76f731900e9d8a382984
    # if not isOcMounted(): sys.exit()

    providerID='0x57b60037b82154ec7149142c606ba024fbb0f991'
    providerAddress = web3.toChecksumAddress(providerID)

    blockReadFrom, availableCoreNum, priceCoreMin, priceDataTransfer, priceStorage, priceCache = eBlocBroker.functions.getProviderInfo(providerAddress).call()
    my_filter = eBlocBroker.eventFilter('LogProvider',{ 'fromBlock': int(blockReadFrom),
                                                      'toBlock': int(blockReadFrom) + 1})
    fID = my_filter.get_all_entries()[0].args['fID']

    if tarHash is None:
        folderToShare = 'exampleFolderToShare' # Path of folder to share
        tarHash = eudatInitializeFolder(folderToShare, oc)

    time.sleep(1)
    print(singleFolderShare(tarHash, oc, fID))
    # subprocess.run(['python', 'singleFolderShare.py', tarHash])

    print('\nSubmitting Job...')
    coreNum    = 1
    coreMinute = 5
    dataTransferIn  = 100
    dataTransferOut = 100
    gasBandwidthMB  = dataTransferIn + dataTransferOut
    gasStorageHour  = 1
    storageID = 1
    accountID = 0

    cacheType = lib.cacheType.private
    # cacheType = lib.cacheType.public

    tx_hash = submitJob(str(providerID), str(tarHash), coreNum, coreMinute, dataTransferIn, dataTransferOut,
                    storageID, str(tarHash), cacheType, gasStorageHour, accountID)

    tx_hash = tx_hash[0]
    print('Tx_hash: ' + tx_hash)
    print('Waiting job to be deployed...')
    while True:
        receipt = web3.eth.getTransactionReceipt(tx_hash)
        if receipt is None:
            time.sleep(2)
            receipt = web3.eth.getTransactionReceipt(tx_hash)
        else:
            logs = eBlocBroker.events.LogJob().processReceipt(receipt)
            print('Job\'s index is ' + str(logs[0].args['index']))
            break

if __name__ == "__main__":
    oc = owncloud.Client('https://b2drop.eudat.eu/')
    oc.login('059ab6ba-4030-48bb-b81b-12115f531296', 'qPzE2-An4Dz-zdLeK-7Cx4w-iKJm9')

    if(len(sys.argv) == 2):
        print('Provided hash=' + sys.argv[1]) # tarHash = '656e8fca04058356f180ae4ff26c33a8'
        eudatSubmitJob(oc, sys.argv[1])
    else:
        eudatSubmitJob(oc)
