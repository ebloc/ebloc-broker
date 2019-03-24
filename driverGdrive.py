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

def log(strIn, color=''): 
   if color != '':
       print(stylize(strIn, fg(color))) 
   else:
       print(strIn)
       
   txFile = open(lib.LOG_PATH + '/transactions/clusterOut.txt', 'a') 
   txFile.write(strIn + "\n") 
   txFile.close()   
   fname = lib.LOG_PATH + '/transactions/' + jobKey + '_' + index + '_driverOutput' + '.txt'
   txFile = open(fname, 'a') 
   txFile.write(strIn + "\n") 
   txFile.close() 
    
def cache(userID, resultsFolderPrev, folderName, sourceCodeHash, folderType):
    if cacheType == 'private': # First checking does is already exist under public cache directory
        globals()['globalCachePath'] = lib.PROGRAM_PATH + '/cache'
        if not os.path.isdir(globalCachePath): # If folder does not exist
            os.makedirs(globalCachePath)
            
        cachedTarFile = globalCachePath + '/' + folderName        
        if folderType == 'gzip':
           if os.path.isfile(cachedTarFile):
              res = subprocess.check_output(['bash', lib.EBLOCPATH + '/scripts/generateMD5sum.sh', cachedTarFile]).decode('utf-8').strip()
              if res == sourceCodeHash: #Checking is already downloaded folder's hash matches with the given hash
                 log('Already cached within public cache directory...', 'green')
                 globals()['cacheType'] = 'public'
                 return True, ''
        elif folderType == 'folder':
           if os.path.isfile(globalCachePath + '/' + folderName + '/run.sh'):              
              res = subprocess.check_output(['bash', lib.EBLOCPATH + '/scripts/generateMD5sum.sh', globalCachePath + '/' + folderName]).decode('utf-8').strip()                
              if res == sourceCodeHash: #Checking is already downloaded folder's hash matches with the given hash
                 log('Already cached within public cache directory...', 'green')
                 globals()['cacheType'] = 'public'
                 return True, ''
             
    if cacheType == 'private' or cacheType == 'public':
        if cacheType == 'private':
            globals()['globalCachePath'] = lib.PROGRAM_PATH + '/' + userID + '/cache'
        elif cacheType == 'public':
            globals()['globalCachePath'] = lib.PROGRAM_PATH + '/cache'
        
        if not os.path.isdir(globalCachePath): # If folder does not exist
            os.makedirs(globalCachePath)
            
        cachedTarFile = globalCachePath + '/' + folderName        

        if folderType == 'gzip':
           if not os.path.isfile(cachedTarFile):
              if not gdriveDownloadFolder(globalCachePath, folderName, folderType): return False
              if not lib.isRunExistInTar(cachedTarFile):
                 lib.silentremove(cachedTarFile)
                 return False, ''              
           else:
              res = subprocess.check_output(['bash', lib.EBLOCPATH + '/scripts/generateMD5sum.sh', cachedTarFile]).decode('utf-8').strip()
              if res == sourceCodeHash: #Checking is already downloaded folder's hash matches with the given hash
                 log('Already cached ...', 'green')
              else:
                 if not gdriveDownloadFolder(globalCachePath, folderName, folderType): return
        elif folderType == 'folder':
           if os.path.isfile(globalCachePath + '/' + folderName + '/run.sh'):              
              res = subprocess.check_output(['bash', lib.EBLOCPATH + '/scripts/generateMD5sum.sh', globalCachePath + '/' + folderName]).decode('utf-8').strip()                
              if res == sourceCodeHash: #Checking is already downloaded folder's hash matches with the given hash
                 log('Already cached ...', 'green')
              else:                 
                 if not gdriveDownloadFolder(globalCachePath, folderName, folderType): return False
                 #os.rename(globalCachePath + '/' + folderName, globalCachePath + '/' + jobKey)
           else:                 
              if not gdriveDownloadFolder(globalCachePath, folderName, folderType): return False
              # os.rename(globalCachePath + '/' + folderName, globalCachePath + '/' + jobKey)              
    elif cacheType == 'ipfs':
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

def gdriveDownloadFolder(resultsFolderPrev, folderName, folderType):    
    if folderType == 'folder':
        # cmd: gdrive download --recursive $jobKey --force --path $resultsFolderPrev  # Gets the source  %TODOTODO
        res, status = lib.subprocessCallAttempt(['gdrive', 'download', '--recursive', jobKey, '--force', '--path', resultsFolderPrev], 1000)        
        # res= subprocess.check_output(['gdrive', 'download', '--recursive', jobKey, '--force', '--path', resultsFolderPrev]).decode('utf-8') #TODO: convert into try except        
    else:
        # cmd: gdrive download $jobKey --force --path $resultsFolder/../
        res, status = lib.subprocessCallAttempt(['gdrive', 'download', jobKey, '--force', '--path', resultsFolderPrev], 1000)
        # res = subprocess.check_output(['gdrive', 'download', jobKey, '--force', '--path', resultsFolderPrev]).decode('utf-8').strip() #TODO: delete
    
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
            log('dataTransferIn=' + str(dataTransferIn) + ' MB | Rounded=' + str(int(dataTransferIn)) + ' MB', 'green')    
    else:
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
            log('dataTransferIn=' + str(dataTransferIn) + ' MB | Rounded=' + str(int(dataTransferIn)) + ' MB', 'green')
            
    return True
    
def driverGdrive(jobKey, index, storageID, userID, sourceCodeHash, cacheType_, eBlocBroker, web3):        
   globals()['jobKey'] = jobKey
   globals()['index'] = index
   # globals()['storageID'] = storageID
   shareToken = -1
   globals()['cacheType'] = str(lib.cacheType.reverse_mapping[cacheType_])
   
   log("key="   + jobKey) 
   log("index=" + index) 

   resultsFolderPrev = lib.PROGRAM_PATH + "/" + userID + "/" + jobKey + "_" + index 
   resultsFolder     = resultsFolderPrev + '/JOB_TO_RUN'    
   
   if not os.path.isdir(resultsFolderPrev): # If folder does not exist
      os.makedirs(resultsFolderPrev)
      os.makedirs(resultsFolder)

   #cmd: gdrive info $jobKey -c $GDRIVE_METADATA # stored for both pipes otherwise its read and lost
   gdriveInfo, status = lib.subprocessCallAttempt(['gdrive', 'info', jobKey, '-c', lib.GDRIVE_METADATA], 1000)
   if not status: return False
   
   mimeType   = lib.getMimeType(gdriveInfo)
   folderName = lib.getFolderName(gdriveInfo)
   
   log('mimeType='   + mimeType)
   log('folderName=' + folderName)
   log("cacheType="  + cacheType)

   if cacheType == 'private' or cacheType == 'public':
      if 'folder' in mimeType: # Recieved job is in folder format
         if cacheType != 'none': 
             check, ipfsHash = cache(userID, resultsFolderPrev, folderName, sourceCodeHash, 'folder')
         if not check: return   
         subprocess.run(['rsync', '-avq', '--partial-dir', '--omit-dir-times', globalCachePath + '/' + folderName + '/', resultsFolder])      
      elif 'gzip' in mimeType: # Recieved job is in folder tar.gz
         if cacheType != 'none':
             check, ipfsHash = cache(userID, resultsFolderPrev, folderName, sourceCodeHash, 'gzip')
         if not check: return   
         subprocess.run(['tar', '-xf', globalCachePath + '/' + folderName, '--strip-components=1', '-C', resultsFolder])
      elif 'zip' in mimeType: # Recieved job is in zip format
         if cacheType != 'none': 
             check, ipfsHash = cache(userID, resultsFolderPrev, folderName, sourceCodeHash, 'zip')
         if not check: return   
         # cmd: unzip -o $resultsFolderPrev/$folderName -d $resultsFolder
         subprocess.run(['unzip', '-o', resultsFolderPrev + '/' + folderName, '-d', resultsFolder])             
         lib.silentremove(resultsFolderPrev + '/' + folderName)
      else:
         return False
   elif cacheType == 'ipfs':
      if 'folder' in mimeType:
         if cacheType != 'none':
             check, ipfsHash = cache(userID, resultsFolderPrev, folderName, sourceCodeHash, 'folder')
         if not check: return   
         log('Reading from IPFS hash=' + ipfsHash)
         # Copy from cached IPFS folder into user's path           
         subprocess.run(['ipfs', 'get', ipfsHash, '-o', resultsFolder]) # cmd: ipfs get <ipfs_hash> -o .
      elif 'gzip' in mimeType:
         if cacheType != 'none':
             check, ipfsHash = cache(userID, resultsFolderPrev, folderName, sourceCodeHash, 'gzip')
         if not check: return            
         log('Reading from IPFS hash=' + ipfsHash)
         subprocess.run(['tar', '-xf', '/ipfs/' + ipfsHash, '--strip-components=1', '-C', resultsFolder])

   lib.sbatchCall(jobKey, index, storageID, str(shareToken), userID,
                  resultsFolder, resultsFolderPrev, dataTransferIn, eBlocBroker,  web3)
