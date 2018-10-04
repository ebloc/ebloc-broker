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

jobKeyGlobal    = None
indexGlobal     = None
storageIDGlobal = None
cacheTypeGlobal = None
shareTokenGlobal = '-1'

# Paths===================================================
ipfsHashes       = lib.PROGRAM_PATH 
# =========================================================

def log(strIn, color=''): #{
   if color != '':
       print(stylize(strIn, fg(color))) 
   else:
       print(strIn)
       
   txFile = open(lib.LOG_PATH + '/transactions/clusterOut.txt', 'a') 
   txFile.write(strIn + "\n") 
   txFile.close() 

   fname = lib.LOG_PATH + '/transactions/' + jobKeyGlobal + '_' + indexGlobal + '_driverOutput' + '.txt'
   txFile = open(fname, 'a') 
   txFile.write(strIn + "\n") 
   txFile.close() 
#}

def getMimeType(gdriveInfo): #{
   # cmd: echo gdriveInfo | grep \'Mime\' | awk \'{print $2}\'
   p1 = subprocess.Popen(['echo', gdriveInfo], stdout=subprocess.PIPE)
   #-----------
   p2 = subprocess.Popen(['grep', 'Mime'], stdin=p1.stdout, stdout=subprocess.PIPE)
   p1.stdout.close()
   #-----------
   p3 = subprocess.Popen(['awk', '{print $2}'], stdin=p2.stdout,stdout=subprocess.PIPE)
   p2.stdout.close()
   #-----------
   return p3.communicate()[0].decode('utf-8').strip()
#}    

def getFolderName(gdriveInfo): #{
   # cmd: echo gdriveInfo | grep \'Name\' | awk \'{print $2}\'
   p1 = subprocess.Popen(['echo', gdriveInfo], stdout=subprocess.PIPE)
   #-----------
   p2 = subprocess.Popen(['grep', 'Name'], stdin=p1.stdout, stdout=subprocess.PIPE)
   p1.stdout.close()
   #-----------
   p3 = subprocess.Popen(['awk', '{print $2}'], stdin=p2.stdout,stdout=subprocess.PIPE)
   p2.stdout.close()
   #-----------
   return p3.communicate()[0].decode('utf-8').strip()    
#}

def gdriveDownloadCheck(res, jobKey, resultsFolderPrev, folderName, folderType): #{
    flag = 1
    tryCount = 0
    while ('googleapi: Error 403' in res) or ('googleapi: Error 403: Rate Limit Exceeded, rateLimitExceeded' in res) or ('googleapi' in res and 'error' in res):
        if tryCount is 5:
            return False
        time.sleep(10)            
        # cmd: gdrive download --recursive $jobKey --force --path $resultsFolderPrev  # Gets the source 
        res= subprocess.check_output(['gdrive', 'download', '--recursive', jobKey, '--force', '--path', resultsFolderPrev]).decode('utf-8').strip()
        log(res)
        flag = 0
        tryCount += 1        

    if flag is 1: log(res)

    if folderType == 'folder':
        if not os.path.isdir(resultsFolderPrev + '/' + folderName): # Check before move operation
            log('Folder is not downloaded successfully.', 'red')
            return False
    else:
        if not os.path.isfile(resultsFolderPrev + '/' + folderName):
            log('File is not downloaded successfully.', 'red')
            return False
    return True
#}
    
def driverGdrive(jobKey, index, storageID, userID, eBlocBroker, web3): #{
   global jobKeyGlobal
   global indexGlobal
   global storageIDGlobal
   global shareTokenGlobal
   
   jobKeyGlobal = jobKey  
   indexGlobal  = index 
   storageIDGlobal = storageID
   
   log("key: "   + jobKey) 
   log("index: " + index) 

   resultsFolderPrev = lib.PROGRAM_PATH + "/" + userID + "/" + jobKey + "_" + index 
   resultsFolder     = resultsFolderPrev + '/JOB_TO_RUN'    
   
   if not os.path.isdir(lib.PROGRAM_PATH + "/" + userID + "/" + jobKey + "_" + index): # If folder does not exist
       os.makedirs(lib.PROGRAM_PATH + "/" + userID + "/" + jobKey + "_" + index)

   #cmd: gdrive info $jobKey -c $GDRIVE_METADATA # stored for both pipes otherwise its read and lost   
   gdriveInfo = subprocess.check_output(['gdrive', 'info', jobKey, '-c', lib.GDRIVE_METADATA]).decode('utf-8').strip()    
   mimeType   = getMimeType(gdriveInfo)
   folderName = getFolderName(gdriveInfo)
   log('mimeType=' + mimeType)
   log('folderName=' + folderName) 
   
   if 'folder' in mimeType: #{ # Recieved job is in folder format      
      # cmd: gdrive download --recursive $jobKey --force --path $resultsFolderPrev  # Gets the source 
      res= subprocess.check_output(['gdrive', 'download', '--recursive', jobKey, '--force', '--path', resultsFolderPrev]).decode('utf-8') #TODO: convert into try except
      if not gdriveDownloadCheck(res, jobKey, resultsFolderPrev, folderName, 'folder'): return           
     # cmd: mv $resultsFolderPrev/$folderName $resultsFolder
      subprocess.run(['mv', resultsFolderPrev + '/' + folderName, resultsFolder])      
   #}       
   elif 'gzip' in mimeType: # Recieved job is in folder tar.gz
       os.makedirs(resultsFolder, exist_ok=True)  
       # cmd: gdrive download $jobKey --force --path $resultsFolder/../
       res = subprocess.check_output(['gdrive', 'download', jobKey, '--force', '--path', resultsFolderPrev]).decode('utf-8').strip()
       if not gdriveDownloadCheck(res, jobKey, resultsFolderPrev, folderName, 'gzip'): return           

       subprocess.run(['tar', '-xf', resultsFolderPrev + '/' + folderName, '--strip-components=1', '-C', resultsFolder])
       subprocess.run(['rm', '-f', resultsFolderPrev + '/' + folderName])       
   elif 'zip' in mimeType: # Recieved job is in zip format
       os.makedirs(resultsFolder, exist_ok=True)  # Gets the source code
       # cmd: gdrive download $jobKey --force --path $resultsFolderPrev/
       res = subprocess.check_output(['gdrive', 'download', jobKey, '--force', '--path', resultsFolderPrev]).decode('utf-8').strip()
       if not gdriveDownloadCheck(res, jobKey, resultsFolderPrev, folderName, 'zip'): return           

       # cmd: unzip -o $resultsFolderPrev/$folderName -d $resultsFolder
       subprocess.run(['unzip', '-o', resultsFolderPrev + '/' + folderName, '-d', resultsFolder])       
       # cmd: rm -f $resultsFolderPrev/$folderName
       subprocess.run(['rm', '-rf', resultsFolderPrev + '/' + folderName])
   else:
       return 0 

   os.chdir(resultsFolder)       # 'cd' into the working path and call sbatch from there
   lib.sbatchCall(jobKeyGlobal, indexGlobal, storageIDGlobal, shareTokenGlobal, userID, resultsFolder, eBlocBroker,  web3)
#}
