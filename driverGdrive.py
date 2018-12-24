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

globals()['dataTransferIn'] = 0 # if the requested file is already cached, it stays as 0

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

def cache(userID, jobKey, resultsFolderPrev, folderName, sourceCodeHash, folderType):
    if globals()['cacheType'] == 'private': # First checking does is already exist under public cache directory
        globals()['globalCachePath'] = lib.PROGRAM_PATH + '/cache'
        if not os.path.isdir(globals()['globalCachePath']): # If folder does not exist
            os.makedirs(globals()['globalCachePath'])
            
        cachedTarFile = globals()['globalCachePath'] + '/' + folderName        
        if folderType == 'gzip':
           if os.path.isfile(cachedTarFile):
              res = subprocess.check_output(['bash', lib.EBLOCPATH + '/scripts/generateMD5sum.sh', cachedTarFile]).decode('utf-8').strip()
              if res == sourceCodeHash: #Checking is already downloaded folder's hash matches with the given hash
                 log('Already cached within public cache directory...', 'green')
                 globals()['cacheType'] = 'public'
                 return True, ''
        elif folderType == 'folder':
           if os.path.isfile(globals()['globalCachePath'] + '/' + folderName + '/run.sh'):              
              res = subprocess.check_output(['bash', lib.EBLOCPATH + '/scripts/generateMD5sum.sh', globals()['globalCachePath'] + '/' + folderName]).decode('utf-8').strip()                
              if res == sourceCodeHash: #Checking is already downloaded folder's hash matches with the given hash
                 log('Already cached within public cache directory...', 'green')
                 globals()['cacheType'] = 'public'
                 return True, ''
             
    if globals()['cacheType'] == 'private' or globals()['cacheType'] == 'public':
        if globals()['cacheType'] == 'private':
            globals()['globalCachePath'] = lib.PROGRAM_PATH + '/' + userID + '/cache'
        elif globals()['cacheType'] == 'public':
            globals()['globalCachePath'] = lib.PROGRAM_PATH + '/cache'
        
        if not os.path.isdir(globals()['globalCachePath']): # If folder does not exist
            os.makedirs(globals()['globalCachePath'])
            
        cachedTarFile = globals()['globalCachePath'] + '/' + folderName        

        if folderType == 'gzip':
           if not os.path.isfile(cachedTarFile):
              if not gdriveDownloadFolder(jobKey, globals()['globalCachePath'], folderName, folderType): return False
              if not lib.isRunExistInTar(cachedTarFile):
                 lib.silentremove(cachedTarFile)
                 return False, ''              
           else:
              res = subprocess.check_output(['bash', lib.EBLOCPATH + '/scripts/generateMD5sum.sh', cachedTarFile]).decode('utf-8').strip()
              if res == sourceCodeHash: #Checking is already downloaded folder's hash matches with the given hash
                 log('Already cached ...', 'green')
              else:
                 if not gdriveDownloadFolder(jobKey, globals()['globalCachePath'], folderName, folderType): return
        elif folderType == 'folder':
           if os.path.isfile(globals()['globalCachePath'] + '/' + folderName + '/run.sh'):              
              res = subprocess.check_output(['bash', lib.EBLOCPATH + '/scripts/generateMD5sum.sh', globals()['globalCachePath'] + '/' + folderName]).decode('utf-8').strip()                
              if res == sourceCodeHash: #Checking is already downloaded folder's hash matches with the given hash
                 log('Already cached ...', 'green')
              else:                 
                 if not gdriveDownloadFolder(jobKey, globals()['globalCachePath'], folderName, folderType): return False
                 #os.rename(globals()['globalCachePath'] + '/' + folderName, globals()['globalCachePath'] + '/' + jobKey)
           else:                 
              if not gdriveDownloadFolder(jobKey, globals()['globalCachePath'], folderName, folderType): return False
              # os.rename(globals()['globalCachePath'] + '/' + folderName, globals()['globalCachePath'] + '/' + jobKey)              
    elif globals()['cacheType'] == 'ipfs':
        log('Adding from google drive mount point into IPFS...', 'blue')
        if folderType == 'gzip':
           tarFile = lib.GDRIVE_CLOUD_PATH + '/.shared/' + folderName           
           if not os.path.isfile(tarFile):
              # TODO: It takes 3-5 minutes for shared folder/file to show up on the .shared folder
              log('Requested file does not exit on mounted folder. PATH=' + tarFile, 'red')
              return False, ''
           ipfsHash = subprocess.check_output(['ipfs', 'add', tarFile]).decode('utf-8').strip()              
        elif folderType == 'folder':
            folderPath = lib.GDRIVE_CLOUD_PATH + '/.shared/' + folderName
            if not os.path.isdir(folderPath):
               log('Requested folder does not exit on mounted folder. PATH=' + folderPath, 'red')
               return False, ''               
            ipfsHash = subprocess.check_output(['ipfs', 'add', '-r', folderPath]).decode('utf-8').strip()            
            ipfsHash = ipfsHash.splitlines()
            ipfsHash = ipfsHash[int(len(ipfsHash) - 1)] # Last line of ipfs hash output is obtained which has the root folder's hash        
        return True, ipfsHash.split()[1]
    return True, ''

def getMimeType(gdriveInfo): 
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

def getFolderName(gdriveInfo): 
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

def gdriveDownloadFolder(jobKey, resultsFolderPrev, folderName, folderType):
    if folderType == 'folder':  
        # cmd: gdrive download --recursive $jobKey --force --path $resultsFolderPrev  # Gets the source 
        res= subprocess.check_output(['gdrive', 'download', '--recursive', jobKey, '--force', '--path', resultsFolderPrev]).decode('utf-8') #TODO: convert into try except        
    else:
       # cmd: gdrive download $jobKey --force --path $resultsFolder/../
       res = subprocess.check_output(['gdrive', 'download', jobKey, '--force', '--path', resultsFolderPrev]).decode('utf-8').strip()
    
    flag = 1
    tryCount = 0
    while ('googleapi: Error 403' in res) or ('googleapi: Error 403: Rate Limit Exceeded, rateLimitExceeded' in res) or ('googleapi' in res and 'error' in res):
        if tryCount == 5:
            return False
        time.sleep(10)            
        # cmd: gdrive download --recursive $jobKey --force --path $resultsFolderPrev  # Gets the source 
        res= subprocess.check_output(['gdrive', 'download', '--recursive', jobKey, '--force', '--path', resultsFolderPrev]).decode('utf-8').strip()
        log(res)
        flag = 0
        tryCount += 1
        
    if flag == 1:
        log(res)

    if folderType == 'folder':
        if not os.path.isdir(resultsFolderPrev + '/' + folderName): # Check before move operation
            log('Folder is not downloaded successfully.', 'red')
            return False
        else:
            p1 = subprocess.Popen(['du', '-sb', resultsFolderPrev + '/' + folderName], stdout=subprocess.PIPE)
            #-----------
            p2 = subprocess.Popen(['awk', '{print $1}'], stdin=p1.stdout, stdout=subprocess.PIPE)
            p1.stdout.close()
            #-----------
            globals()['dataTransferIn'] = p2.communicate()[0].decode('utf-8').strip() # Retunrs downloaded files size in bytes
            globals()['dataTransferIn'] =  int(globals()['dataTransferIn']) * 0.000001
            log('dataTransferIn=' + str(globals()['dataTransferIn']) + ' MB | Rounded=' + str(int(globals()['dataTransferIn'])) + ' MB', 'green')    
    else:
        print(resultsFolderPrev + '/' + folderName)
        if not os.path.isfile(resultsFolderPrev + '/' + folderName):
            log('File is not downloaded successfully.', 'red')
            return False
        else:
            p1 = subprocess.Popen(['ls', '-ln', resultsFolderPrev + '/' + folderName], stdout=subprocess.PIPE)
            #-----------
            p2 = subprocess.Popen(['awk', '{print $5}'], stdin=p1.stdout, stdout=subprocess.PIPE)
            p1.stdout.close()
            #-----------
            globals()['dataTransferIn'] = p2.communicate()[0].decode('utf-8').strip() # Returns downloaded files size in bytes
            globals()['dataTransferIn'] =  int(globals()['dataTransferIn']) * 0.000001
            log('dataTransferIn=' + str(globals()['dataTransferIn']) + ' MB | Rounded=' + str(int(globals()['dataTransferIn'])) + ' MB', 'green')
    return True
    
def driverGdrive(jobKey, index, storageID, userID, sourceCodeHash, cacheType, eBlocBroker, web3):        
   globals()['jobKey'] = jobKey
   globals()['index'] = index
   globals()['storageID'] = storageID
   shareToken = -1
   globals()['cacheType'] = lib.cacheType.reverse_mapping[cacheType]
   
   log("key="   + jobKey) 
   log("index=" + index) 

   resultsFolderPrev = lib.PROGRAM_PATH + "/" + userID + "/" + jobKey + "_" + index 
   resultsFolder     = resultsFolderPrev + '/JOB_TO_RUN'    
   
   if not os.path.isdir(lib.PROGRAM_PATH + "/" + userID + "/" + jobKey + "_" + index): # If folder does not exist
      os.makedirs(resultsFolderPrev)
      os.makedirs(resultsFolder)

   #cmd: gdrive info $jobKey -c $GDRIVE_METADATA # stored for both pipes otherwise its read and lost
   gdriveInfo = subprocess.check_output(['gdrive', 'info', jobKey, '-c', lib.GDRIVE_METADATA]).decode('utf-8').strip()   
   mimeType   = getMimeType(gdriveInfo)
   folderName = getFolderName(gdriveInfo)
   
   log('mimeType='   + mimeType)
   log('folderName=' + folderName)
   log("cacheType="  + str(globals()['cacheType']))

   if globals()['cacheType'] == 'private' or globals()['cacheType'] == 'public':
      if 'folder' in mimeType: # Recieved job is in folder format
         if globals()['cacheType'] != 'none': 
             check, ipfsHash = cache(userID, jobKey, resultsFolderPrev, folderName, sourceCodeHash, 'folder')
         if not check: return   
         subprocess.run(['rsync', '-avq', '--partial-dir', '--omit-dir-times', globals()['globalCachePath'] + '/' + folderName + '/', resultsFolder])      
      elif 'gzip' in mimeType: # Recieved job is in folder tar.gz
         if globals()['cacheType'] != 'none':
             check, ipfsHash = cache(userID, jobKey, resultsFolderPrev, folderName, sourceCodeHash, 'gzip')
         if not check: return   
         subprocess.run(['tar', '-xf', globals()['globalCachePath'] + '/' + folderName, '--strip-components=1', '-C', resultsFolder])
      elif 'zip' in mimeType: # Recieved job is in zip format
         if globals()['cacheType'] != 'none': 
             check, ipfsHash = cache(userID, jobKey, resultsFolderPrev, folderName, sourceCodeHash, 'zip')
         if not check: return   
         # cmd: unzip -o $resultsFolderPrev/$folderName -d $resultsFolder
         subprocess.run(['unzip', '-o', resultsFolderPrev + '/' + folderName, '-d', resultsFolder])             
         lib.silentremove(resultsFolderPrev + '/' + folderName)
      else:
         return False
   elif globals()['cacheType'] == 'ipfs':
      if 'folder' in mimeType:
         if globals()['cacheType'] != 'none':
             check, ipfsHash = cache(userID, jobKey, resultsFolderPrev, folderName, sourceCodeHash, 'folder')
         if not check: return   
         log('Reading from IPFS hash=' + ipfsHash)
         # Copy from cached IPFS folder into user's path           
         subprocess.run(['ipfs', 'get', ipfsHash, '-o', resultsFolder]) # cmd: ipfs get <ipfs_hash> -o .
      elif 'gzip' in mimeType:
         if globals()['cacheType'] != 'none':
             check, ipfsHash = cache(userID, jobKey, resultsFolderPrev, folderName, sourceCodeHash, 'gzip')
         if not check: return            
         log('Reading from IPFS hash=' + ipfsHash)
         subprocess.run(['tar', '-xf', '/ipfs/' + ipfsHash, '--strip-components=1', '-C', resultsFolder])
   os.chdir(resultsFolder)       # 'cd' into the working path and call sbatch from there
   lib.sbatchCall(globals()['jobKey'], globals()['index'], globals()['storageID'], str(shareToken), userID,
                  resultsFolder, globals()['dataTransferIn'], eBlocBroker,  web3)
