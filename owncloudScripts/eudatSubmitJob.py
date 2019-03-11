#!/usr/bin/env python3

import os, owncloud, subprocess, sys, time
sys.path.insert(1, os.path.join(sys.path[0], '..'))
import lib

sys.path.insert(0, './contractCalls')
from contractCalls.submitJob import submitJob
from isOcMounted             import isOcMounted

from lib_owncloud import singleFolderShare
from lib_owncloud import eudatInitializeFolder
from lib_owncloud import isOcMounted

def eudatSubmitJob(oc, tarHash=None): # fc33e7908fdf76f731900e9d8a382984        
    if not isOcMounted():
        sys.exit()
        
    clusterID='0x4e4a0750350796164D8DefC442a712B7557BF282'
    if tarHash is None:
        folderToShare = 'exampleFolderToShare' # Path of folder to share
        tarHash = eudatInitializeFolder(folderToShare, oc)

    time.sleep(1)
    print(singleFolderShare(tarHash, oc))
    # subprocess.run(['python', 'singleFolderShare.py', tarHash])

    print('\nSubmitting Job...')    
    coreNum=1
    coreMinuteGas=5

    dataTransferIn  = 100
    dataTransferOut = 100
    gasBandwidthMB    = dataTransferIn + dataTransferOut
    gasStorageHour  = 1
    
    jobDescription = 'Science'
    storageID = 1
    accountID = 0

    cacheType = lib.cacheType.private
    # cacheType = lib.cacheType.public
    
    res = submitJob(str(clusterID), str(tarHash), coreNum, coreMinuteGas, dataTransferIn, dataTransferOut,
                    storageID, str(tarHash), cacheType, gasStorageHour, accountID)
    print('Tx_hash: ' + res)

if __name__ == "__main__":
    oc = owncloud.Client('https://b2drop.eudat.eu/')
    oc.login('059ab6ba-4030-48bb-b81b-12115f531296', 'qPzE2-An4Dz-zdLeK-7Cx4w-iKJm9')

    if(len(sys.argv) == 2):
        print('Provided hash=' + sys.argv[1]) # tarHash = '656e8fca04058356f180ae4ff26c33a8'
        eudatSubmitJob(oc, sys.argv[1])
    else:
        eudatSubmitJob(oc)
