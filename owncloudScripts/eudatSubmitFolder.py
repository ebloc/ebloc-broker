#!/usr/bin/env python3

import os, owncloud, subprocess, sys, time
import lib
from contractCalls.submitJob import submitJob
from lib_owncloud import isOcMounted
from lib_owncloud import singleFolderShare
from imports import connectEblocBroker, getWeb3

web3        = getWeb3()
eBlocBroker = connectEblocBroker(web3)

oc = owncloud.Client('https://b2drop.eudat.eu/')
oc.login('059ab6ba-4030-48bb-b81b-12115f531296', 'qPzE2-An4Dz-zdLeK-7Cx4w-iKJm9')

def eudatSubmitJob(tarHash=None):
    clusterID='0x4e4a0750350796164D8DefC442a712B7557BF282'
    clusterAddress = web3.toChecksumAddress(clusterID)
    blockReadFrom, availableCoreNum, priceCoreMin, priceDataTransfer, priceStorage, priceCache = eBlocBroker.functions.getClusterInfo(clusterAddress).call()
    my_filter = eBlocBroker.eventFilter('LogCluster',{ 'fromBlock': int(blockReadFrom),
                                                      'toBlock': int(blockReadFrom) + 1})
    fID = my_filter.get_all_entries()[0].args['fID']
    
    if tarHash is None:
        folderToShare = 'exampleFolderToShare'    
        subprocess.run(['sudo', 'chmod', '-R', '777', folderToShare])        
        tarHash = subprocess.check_output(['../scripts/generateMD5sum.sh', folderToShare]).decode('utf-8').strip()                        
        tarHash = tarHash.split(' ', 1)[0]
        print('hash=' + tarHash)
        subprocess.run(['rm', '-rf', tarHash])
        subprocess.run(['cp', '-a', folderToShare + '/', tarHash])
        res = oc.put_directory('./', tarHash)
        if not res:
            sys.exit()            
            
    time.sleep(1)
    print(singleFolderShare(tarHash, oc, fID))
    # subprocess.run(['python', 'singleFolderShare.py', tarHash])
    print('\nSubmitting Job...')
    coreNum=1
    coreMinuteGas=5
    jobDescription='science'
    storageID=1
    accountID=0

    res = submitJob(str(clusterID), str(tarHash), coreNum, coreMinuteGas, str(jobDescription), storageID, str(tarHash), accountID)
    print(res)

if __name__ == "__main__":
    if(len(sys.argv) == 2):
        print('Provided hash=' + sys.argv[1]) # tarHash = '656e8fca04058356f180ae4ff26c33a8'
        eudatSubmitJob(sys.argv[1])
    else:
        eudatSubmitJob()
