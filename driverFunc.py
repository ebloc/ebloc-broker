#!/usr/bin/env python3

import owncloud, hashlib, getpass, sys, os, time, subprocess, lib, re
from datetime import datetime, timedelta
from   subprocess import call
import os.path
from colored import stylize
from colored import fg
import subprocess
import glob, errno
from contractCalls.getJobInfo import getJobInfo

globals()['shareToken'] = '-1'
# Paths===================================================
ipfsHashes       = lib.PROGRAM_PATH 
# =========================================================

def log(strIn, color=''):
    if color != '':
        print(stylize(strIn, fg(color))) 
    else:
        print(strIn)
       
    txFile = open(lib.LOG_PATH + '/transactions/clusterOut.txt', 'a') 
    txFile.write(strIn + "\n") 
    txFile.close() 
    fname = lib.LOG_PATH + '/transactions/' + globals()['jobKey'] + '_' + globals()['index'] + '_driverOutput' + '.txt'
    txFile = open(fname, 'a') 
    txFile.write(strIn + "\n") 
    txFile.close() 

def driverGithub(jobKey, index, storageID, userID, cacheType, eBlocBroker, web3):
   globals()['jobKey']    = jobKey
   globals()['index']     = index
   globals()['storageID'] = storageID
  
   jobKeyGit = str(jobKey).replace("=", "/")
   dataTransferIn = 0 # if the requested file is already cached, it stays as 0                
   
   log("key="   + jobKey) 
   log("index=" + index)
   resultsFolderPrev = lib.PROGRAM_PATH  + "/" + userID + "/" + jobKey + "_" + index
   resultsFolder     = resultsFolderPrev + '/JOB_TO_RUN'   
   if not os.path.isdir(resultsFolderPrev): # If folder does not exist
      os.makedirs(lib.PROGRAM_PATH + "/" + userID + "/" + jobKey + "_" + index)

   # cmd: git clone https://github.com/$jobKeyGit.git $resultsFolder
   subprocess.run(['git', 'clone', 'https://github.com/' + jobKeyGit + '.git', resultsFolder]) # Gets the source code   
   # TODO: calculate dataTransferIn for the downloaded job.
   lib.sbatchCall(globals()['jobKey'], globals()['index'], globals()['storageID'], globals()['shareToken'], userID, resultsFolder, resultsFolderPrev,
                  dataTransferIn, eBlocBroker,  web3)

def driverIpfs(jobKey, index, storageID, userID, cacheType, eBlocBroker, web3):
    globals()['jobKey']    = jobKey
    globals()['index']     = index
    globals()['storageID'] = storageID
              
    lib.isIpfsOn()  
    log("jobKey=" + jobKey)
    isHashCached = lib.isHashCached(jobKey)
    log("isHashCached=" + str(isHashCached))    

    dataTransferIn    = 0 # if the requested file is already cached, it stays as 0                
    resultsFolderPrev = lib.PROGRAM_PATH + "/" + userID + "/" + jobKey + "_" + index
    resultsFolder     = resultsFolderPrev + '/JOB_TO_RUN'           

    if not os.path.isdir(resultsFolderPrev): # If folder does not exist
       os.makedirs(resultsFolderPrev, exist_ok=True) 
       os.makedirs(resultsFolder,     exist_ok=True) 

    if os.path.isfile(resultsFolder + '/' + jobKey):
       lib.silentremove(resultsFolder + '/' + jobKey)
       
    ipfsCallCounter = 0
    for attempt in range(1):
        log('Attempting to get IPFS file...', 'light_salmon_3b')
        # IPFS_PATH=$HOME"/.ipfs" && export IPFS_PATH TODO: Probably not required
        # cmd: timeout 300 ipfs object stat $jobKey
        isIPFSHashExist, status = lib.runCommand(['timeout', '300', 'ipfs', 'object', 'stat', jobKey]) # Wait Max 5 minutes.
        if not status:
            log('Error: Failed to get IPFS file...', 'red')
        else:
            log(isIPFSHashExist)
            for item in isIPFSHashExist.split("\n"):
                if "CumulativeSize" in item:
                    cumulativeSize = item.strip().split()[1]
                    break
                    # log(cumulativeSize)
            break # Success
    else:
        return False
      
    if "CumulativeSize" in isIPFSHashExist:
        # IPFS_PATH=$HOME"/.ipfs" && export IPFS_PATH TODO: Probably not required
        # TODO try -- catch yap code run olursa ayni dosya'ya get ile dosyayi cekemiyor
        # cmd: ipfs get $jobKey --output=$resultsFolder
        res = subprocess.check_output(['ipfs', 'get', jobKey, '--output=' + resultsFolder]).decode('utf-8').strip() # Wait Max 5 minutes.
        print(res)
        if not isHashCached:
            dataTransferIn = cumulativeSize
            dataTransferIn =  int(dataTransferIn) * 0.000001
            log('dataTransferIn=' + str(dataTransferIn) + ' MB | Rounded=' + str(int(dataTransferIn)) + ' MB', 'green')
            '''
            if cacheType != 'none': # TODO: pin if storage is paid
                res = subprocess.check_output(['ipfs', 'pin', 'add', jobKey]).decode('utf-8').strip() # pin downloaded ipfs hash
                print(res)
            '''

        if storageID == '2': # Case for the ipfsMiniLock
            with open(lib.LOG_PATH + '/private/miniLockPassword.txt', 'r') as content_file:
                passW = content_file.read().strip()

            # cmd: mlck decrypt -f $resultsFolder/$jobKey --passphrase="$passW" --output-file=$resultsFolder/output.tar.gz
            res, status  = lib.runCommand(['mlck', 'decrypt', '-f', resultsFolder + '/' + jobKey,
                                         '--passphrase=' + passW,
                                         '--output-file=' + resultsFolder + '/output.tar.gz'])
            log("mlck decrypt status=" + str(status))
            passW = None
            # cmd: tar -xvf $resultsFolder/output.tar.gz -C resultsFolder
            subprocess.run(['tar', '-xvf', resultsFolder + '/output.tar.gz', '-C', resultsFolder])
            lib.silentremove(resultsFolder + '/' + jobKey)
            lib.silentremove(resultsFolder + '/output.tar.gz')
                        
        if not os.path.isfile(resultsFolder + '/run.sh'): 
            log("run.sh does not exist", 'red') 
            return False 
    else:
        log("Error: !!!!!!!!!!!!!!!!!!!!!!! Markle not found! timeout for ipfs object stat retrieve !!!!!!!!!!!!!!!!!!!!!!!", 'red')  # IPFS file could not be accessed
        return False
   
    lib.sbatchCall(globals()['jobKey'], globals()['index'], globals()['storageID'], globals()['shareToken'], userID,
                   resultsFolder, resultsFolderPrev, dataTransferIn, eBlocBroker,  web3)

# To test driverFunc.py executed as script.
if __name__ == '__main__':
   var       = "QmefdYEriRiSbeVqGvLx15DKh4WqSMVL8nT4BwvsgVZ7a5"
   index     = "1"
   storageID = "0"

   driverIpfs(var, index, storageID) 
