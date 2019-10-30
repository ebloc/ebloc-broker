#!/usr/bin/env python3

import os, owncloud, subprocess, sys, time, pprint

from lib import StorageID, CacheType
from contractCalls.submitJob       import submitJob
from contractCalls.getProviderInfo import getProviderInfo
from contract.scripts.lib          import cost

from imports      import connect, connectEblocBroker, getWeb3
from isOcMounted  import isOcMounted
from lib_owncloud import singleFolderShare
from lib_owncloud import eudatInitializeFolder
from lib_owncloud import isOcMounted

def eudatSubmitJob(provider, oc, eBlocBroker=None, w3=None): # fc33e7908fdf76f731900e9d8a382984
    accountID = 0    
    eBlocBroker, w3 = connect(eBlocBroker, w3)        
    if eBlocBroker is None or w3 is None:        
        return False, 'web3 is not connected'

    # if not isOcMounted():
    #     return False, 'owncloud is not connected'
    
    provider =  w3.toChecksumAddress(provider) # netlab
    status, providerInfo = getProviderInfo(provider, eBlocBroker, w3)    
    folderToShare_list  = [] # Path of folder to share
    sourceCodeHash_list = []
    cacheHour_list      = []
    coreMin_list        = []

    # Full path of the sourceCodeFolders is given
    folderToShare_list.append('/home/netlab/eBlocBroker/owncloudScripts/exampleFolderToShare/sourceCode')
    folderToShare_list.append('/home/netlab/eBlocBroker/owncloudScripts/exampleFolderToShare/data1')
    
    for i in range(0, len(folderToShare_list)):                
        folderHash = eudatInitializeFolder(folderToShare_list[i], oc)
        if i == 0:
            jobKey = folderHash

        sourceCodeHash = w3.toBytes(text=folderHash) # required to send string as bytes
        sourceCodeHash_list.append(sourceCodeHash)        
        if not singleFolderShare(folderHash, oc, providerInfo['fID']):
            sys.exit()
        time.sleep(1)        
        
    print('\nSubmitting Job...')
    coreMin_list.append(5)    
    coreNum         = 1
    core_list       = [1]        
    dataTransferIn  = [1, 1]
    dataTransferOut = 1        
    dataTransfer    = [dataTransferIn, dataTransferOut]                
    storageID       = [StorageID.EUDAT.value, StorageID.EUDAT.value]
    cacheType       = CacheType.PUBLIC.value   
    cacheHour_list  = [1, 1]
    print(sourceCodeHash_list)
    
    jobPriceValue, _cost = cost(core_list, coreMin_list, provider, sourceCodeHash_list, dataTransferIn, dataTransferOut, cacheHour_list, storageID, eBlocBroker, w3, False)
    
    status, result = submitJob(provider, jobKey, core_list, coreMin_list, dataTransferIn, dataTransferOut, storageID, sourceCodeHash_list, cacheType, cacheHour_list, accountID, jobPriceValue, eBlocBroker, w3)
    return status, result

if __name__ == "__main__":
    w3          = getWeb3()
    eBlocBroker = connectEblocBroker(w3)

    oc = owncloud.Client('https://b2drop.eudat.eu/')
    oc.login('059ab6ba-4030-48bb-b81b-12115f531296', 'qPzE2-An4Dz-zdLeK-7Cx4w-iKJm9')
    
    if len(sys.argv) == 3:
        provider = str(sys.argv[1])
        tarHash  = sys.argv[2]
        print('Provided hash=' + tarHash)         
    else:
        provider = "0x57b60037b82154ec7149142c606ba024fbb0f991" # netlab
        
    status, result = eudatSubmitJob(provider, oc, eBlocBroker, w3)    
    if not status:
        print(result)
        sys.exit()
    else:    
        print('tx_hash=' + result)
        receipt = w3.eth.waitForTransactionReceipt(result)
        print("Transaction receipt mined: \n")
        pprint.pprint(dict(receipt))
        print("Was transaction successful?")
        pprint.pprint(receipt['status'])
        if receipt['status'] == 1:
            logs = eBlocBroker.events.LogJob().processReceipt(receipt)
            try:
                print("Job's index=" + str(logs[0].args['index']))
            except IndexError:
                print('Transaction is reverted.')
