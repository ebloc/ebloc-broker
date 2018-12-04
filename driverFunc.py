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
cacheTypeGlobal = None
dataTransferIn  = 0 # if the requested file is already cached, it stays as 0

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

def driverGithub(jobKey, index, storageID, userID, eBlocBroker, web3):
   globals()['jobKey']    = jobKey
   globals()['index']     = index
   globals()['storageID'] = storageID
  
   jobKeyGit       = str(jobKey).replace("=", "/")
   
   log("key: "   + jobKey) 
   log("index: " + index)

   # resultsFolderPrev = lib.PROGRAM_PATH + "/" + userID + "/" + jobKey + "_" + index
   resultsFolder     = lib.PROGRAM_PATH + "/" + userID + "/" + jobKey + "_" + index + '/JOB_TO_RUN'
   
   if not os.path.isdir(lib.PROGRAM_PATH + "/" + userID + "/" + jobKey + "_" + index): # If folder does not exist
      os.makedirs(lib.PROGRAM_PATH + "/" + userID + "/" + jobKey + "_" + index)

   # cmd: git clone https://github.com/$jobKeyGit.git $resultsFolder
   subprocess.run(['git', 'clone', 'https://github.com/' + jobKeyGit + '.git', resultsFolder]) # Gets the source code   
   os.chdir(resultsFolder)  # 'cd' into the working path and call sbatch from there
   lib.sbatchCall(globals()['jobKey'], globals()['index'], globals()['storageID'], globals()['shareToken'], userID, resultsFolder, eBlocBroker,  web3)

def driverIpfs(jobKey, index, storageID, userID, eBlocBroker, web3):
    globals()['jobKey'] = jobKey
    globals()['index']  = index
    globals()['storageID']  = storageID
              
    lib.isIpfsOn()  
    log("jobKey: " + jobKey)
             
    resultsFolderPrev = lib.PROGRAM_PATH + "/" + userID + "/" + jobKey + "_" + index
    resultsFolder     = resultsFolderPrev + '/JOB_TO_RUN'           

    if not os.path.isdir(resultsFolderPrev): # If folder does not exist
       os.makedirs(resultsFolderPrev, exist_ok=True) 
       os.makedirs(resultsFolder,     exist_ok=True) 

    os.chdir(resultsFolder)  # 'cd' into the working path and call sbatch from there
    
    if os.path.isfile(jobKey):
       subprocess.run(['rm', '-f', jobKey])

    ipfsCallCounter = 0
    while True:
        try:
            # cmd: timeout 300 ipfs object stat $jobKey
            # IPFS_PATH=$HOME"/.ipfs" && export IPFS_PATH TODO: Probably not required
            isIPFSHashExist = subprocess.check_output(['timeout', '300', 'ipfs', 'object', 'stat', jobKey]).decode('utf-8').strip() # Wait Max 5 minutes.
            log(isIPFSHashExist)
            break
        except subprocess.CalledProcessError as e: # Catches resource temporarily unavailable on ipfs
            log(e.output.decode('utf-8').strip(), 'red')
            if ipfsCallCounter == 5:
                return False
            ipfsCallCounter += 1
            time.sleep(10)
    if "CumulativeSize" in isIPFSHashExist:
       # cmd: ipfs get $jobKey --output=$resultsFolder
       # IPFS_PATH=$HOME"/.ipfs" && export IPFS_PATH TODO: Probably not required
       # TODO try -- catch yap code run olursa ayni dosya'ya get ile dosyayi cekemiyor 
       res = subprocess.check_output(['ipfs', 'get', jobKey, '--output=' + resultsFolder]).decode('utf-8').strip() # Wait Max 5 minutes.
       print(res)
              
       if storageID == '2': # Case for the ipfsMiniLock
          passW = 'bright wind east is pen be lazy usual' 

          # cmd: mlck decrypt -f $resultsFolder/$jobKey --passphrase="$passW" --output-file=$resultsFolder/output.tar.gz
          log(subprocess.check_output(['mlck', 'decrypt', '-f', resultsFolder + '/' + jobKey +
                                       '--passphrase=' + passW,
                                       '--output-file=' + resultsFolder + '/output.tar.gz']).decode('utf-8'))          
          # cmd: rm -f $resultsFolder/$jobKey
          subprocess.run(['rm', '-f', resultsFolder + '/' + jobKey])         
          # cmd: tar -xf $resultsFolder/output.tar.gz
          subprocess.run(['tar', '-xf', resultsFolder + '/output.tar.gz'])          
          # cmd: rm -f $resultsFolder/output.tar.gz
          subprocess.run(['rm', '-f', resultsFolder + '/output.tar.gz'])             
       if not os.path.isfile('run.sh'): 
          log("run.sh does not exist", 'red') 
          return False 
    else:
       log("!!!!!!!!!!!!!!!!!!!!!!! Markle not found! timeout for ipfs object stat retrieve !!!!!!!!!!!!!!!!!!!!!!!", 'red')  # IPFS file could not be accessed
       return False 
    os.chdir(resultsFolder)  # 'cd' into the working path and call sbatch from there
    lib.sbatchCall(globals()['jobKey'], globals()['index'], globals()['storageID'], globals()['shareToken'], userID,
                   resultsFolder, dataTransferIn, eBlocBroker,  web3)

# To test driverFunc.py executed as script.
if __name__ == '__main__':
   var        = "QmefdYEriRiSbeVqGvLx15DKh4WqSMVL8nT4BwvsgVZ7a5"
   index      = "1"
   myType     = "0"

   driverIpfs(var, index, myType) 

