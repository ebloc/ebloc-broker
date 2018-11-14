#!/usr/bin/env python

import os, owncloud, subprocess, sys, time
sys.path.insert(1, os.path.join(sys.path[0], '..'))
import lib

sys.path.insert(0, './contractCalls')
from contractCalls.submitJob import submitJob
from isOcMounted       import isOcMounted
from singleFolderShare import singleFolderShare

oc = owncloud.Client('https://b2drop.eudat.eu/')
oc.login('059ab6ba-4030-48bb-b81b-12115f531296', 'qPzE2-An4Dz-zdLeK-7Cx4w-iKJm9')

def eudatSubmitJob(tarHash=None): #{ # fc33e7908fdf76f731900e9d8a382984
    # if not isOcMounted():
    #     sys.exit()
               
    if tarHash is None:
        folderToShare = 'exampleFolderToShare'    
        subprocess.run(['chmod', '-R', '777', folderToShare])
        subprocess.run(['sudo', 'tar', 'zcf', folderToShare + '.tar.gz', folderToShare])
        tarHash = subprocess.check_output(['md5sum', folderToShare + '.tar.gz']).decode('utf-8').strip()
        tarHash = tarHash.split(' ', 1)[0]
        print('hash=' + tarHash)
        subprocess.run(['mv', folderToShare + '.tar.gz', tarHash + '.tar.gz'])

        res = oc.mkdir(tarHash)
        print(res)

        print('./' + tarHash + '/' + tarHash + '.tar.gz', tarHash + '.tar.gz')
        res = oc.put_file('./' + tarHash + '/' + tarHash + '.tar.gz', tarHash + '.tar.gz')

        if not res:
            sys.exit()
            
        # ocClient='/home/alper/ocClient'
        # res = subprocess.check_output(['sudo', 'rsync', '-avhW', '--progress', tarHash + '.tar.gz', ocClient + '/' + tarHash + '/']).decode('utf-8').strip()
        # print(ocClient + '/' + tarHash) 
        print(res)
        subprocess.run(['rm', '-f', tarHash + '.tar.gz'])
    
    time.sleep(1)
    print(singleFolderShare(tarHash, oc))
    # subprocess.run(['python', 'singleFolderShare.py', tarHash])

    print('\nSubmitting Job...')
    clusterID='0x4e4a0750350796164D8DefC442a712B7557BF282'
    coreNum=1
    coreMinuteGas=5
    jobDescription='science'
    storageID=1
    accountID=0

    res = submitJob(str(clusterID), str(tarHash), coreNum, coreMinuteGas, str(jobDescription), storageID, str(tarHash), accountID)
    print(res)
#}

if __name__ == "__main__":
    if(len(sys.argv) == 2):
        print('Provided hash=' + sys.argv[1]) # tarHash = '656e8fca04058356f180ae4ff26c33a8'
        eudatSubmitJob(sys.argv[1])
    else:
        eudatSubmitJob()
