#!/usr/bin/env python

import hashlib, getpass, sys, os, time, subprocess, lib
from   subprocess import call
import os.path
from colored import stylize
from colored import fg
import subprocess
import glob, errno
from contractCalls.getJobInfo import getJobInfo

global folderType

jobKeyGlobal    = None
indexGlobal     = None
storageIDGlobal = None
cacheTypeGlobal = None
shareTokenGlobal = '-1'
folderType = None

# Paths===================================================
ipfsHashes       = lib.PROGRAM_PATH 
# =========================================================

def silentremove(filename): #{
    try:
        os.remove(filename)
    except OSError as e: # This would be "except OSError, e:" before Python 2.6
       pass
#}

def removeFiles(filename): #{
   if "*" in filename: 
       for fl in glob.glob(filename):
           print(fl)
           silentremove(fl) 
   else:
       silentremove(filename) 
#}

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

def isRunExistInTar(tarPath): #{   
    try:
        FNULL = open(os.devnull, 'w')
        res = subprocess.check_output(['tar', 'ztf', tarPath, '--wildcards', '*/run.sh'], stderr=FNULL).decode('utf-8').strip()
        FNULL.close()
        if res.count('/') == 1: # Main folder should contain the 'run.sh' file
            log('./run.sh exists under the parent folder', 'green')
            return True
        else:
            log('run.sh does not exist under the parent folder', 'red')
            return False            
    except:
        log('run.sh does not exist under the parent folder', 'red')
        return False
#}

def isTarExistsInZip(resultsFolderPrev): #{
    global folderType
    # cmd: unzip -l $resultsFolder/output.zip | grep $eudatFolderName/run.sh
    # Checks does zip contains .tar.gz file or not
    p1 = subprocess.Popen(['unzip', '-l', resultsFolderPrev + '/output.zip'], stdout=subprocess.PIPE)
    #-----------
    p2 = subprocess.Popen(['grep', jobKeyGlobal + '.tar.gz'], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    #-----------
    out = p2.communicate()[0].decode('utf-8').strip()    
    if jobKeyGlobal + '.tar.gz' in out:
        folderType = 'tar.gz'
    else:
        folderType = 'folder'
    log('folderType=' + folderType)
#}

def cache(userID, resultsFolderPrev): #{
    if cacheTypeGlobal is 'local': # Download into local directory at $HOME/.eBlocBroker/cache
        globalCacheFolder = lib.PROGRAM_PATH + '/' + userID + '/cache'
        if not os.path.isdir(globalCacheFolder): # If folder does not exist
            os.makedirs(globalCacheFolder)
                   
        cachedFolder  = lib.PROGRAM_PATH + '/' + userID + '/cache' + '/' + jobKeyGlobal
        cachedTarFile = lib.PROGRAM_PATH + '/' + userID + '/cache' + '/' + jobKeyGlobal + '.tar.gz'

        if not os.path.isfile(cachedTarFile):            
            if os.path.isfile(cachedFolder + '/run.sh'):
                res = subprocess.check_output(['bash', lib.EBLOCPATH + '/scripts/generateMD5sum.sh', cachedFolder]).decode('utf-8').strip()
                if res == jobKeyGlobal: #Checking is already downloaded folder's hash matches with the given hash
                    global folderType
                    folderType = 'folder'
                    log('Already cached ...', 'green')
                    return True, ''
                
            eudatDownloadFolder(globalCacheFolder, cachedFolder)            
            if folderType == 'tar.gz' and not isRunExistInTar(cachedTarFile):
                subprocess.run(['rm', '-f', cachedTarFile])
                return False, ''            
        else:
            res = None
            if folderType == 'tar.gz':
                res = subprocess.check_output(['bash', lib.EBLOCPATH + '/scripts/generateMD5sum.sh', cachedTarFile]).decode('utf-8').strip()
            elif folderType == 'folder':
                res = subprocess.check_output(['bash', lib.EBLOCPATH + '/scripts/generateMD5sum.sh', cachedFolder]).decode('utf-8').strip()

            if res == jobKeyGlobal: #Checking is already downloaded folder's hash matches with the given hash
                log('Already cached ...', 'green')
                return True, ''
            else:
                eudatDownloadFolder(globalCacheFolder, cachedFolder)
    elif cacheTypeGlobal is 'ipfs':
        log('Adding from owncloud mount point into IPFS...', 'blue')
        tarFile = lib.OC + '/' + jobKeyGlobal + '/' + jobKeyGlobal + '.tar.gz'        
        if os.path.isfile(tarFile):            
            folderType = 'tar.gz'
            ipfsHash = subprocess.check_output(['ipfs', 'add', tarFile]).decode('utf-8').strip()
        else:
            folderType = 'folder'
            ipfsHash = subprocess.check_output(['ipfs', 'add', '-r', lib.OC + '/' + jobKeyGlobal]).decode('utf-8').strip()            
            ipfsHash = ipfsHash.splitlines()
            ipfsHash = ipfsHash[int(len(ipfsHash) - 1)] # Last line of ipfs hash output is obtained which has the root folder's hash
        return True, ipfsHash.split()[1]
    return True, ''
#}

# Assume job is sent as .tar.gz file
def eudatDownloadFolder(resultsFolderPrev, resultsFolder): #{
   # cmd: wget -4 -o /dev/stdout https://b2drop.eudat.eu/s/$shareToken/download --output-document=$resultsFolderPrev/output.zip
   log('Downloading output.zip -> ' + resultsFolderPrev + '/output.zip')
   ret = subprocess.check_output(['wget', '-4', '-o', '/dev/stdout', 'https://b2drop.eudat.eu/s/' + shareTokenGlobal +
                                  '/download', '--output-document=' + resultsFolderPrev + '/output.zip']).decode('utf-8')
   if "ERROR 404: Not Found" in ret:
       log(ret, 'red') 
       log('File not found The specified document has not been found on the server.', 'red') 
       # TODO: since folder does not exist, do complete refund to the user.
       return False
   log(ret) 
   isTarExistsInZip(resultsFolderPrev)
   
   time.sleep(0.25) 
   if os.path.isfile(resultsFolderPrev + '/output.zip'):
       if folderType == 'tar.gz':           
           subprocess.run(['unzip', '-jo', resultsFolderPrev + '/output.zip', '-d', resultsFolderPrev, '-x', '*result-*.tar.gz'])
       else:
           subprocess.run(['unzip', '-jo', resultsFolderPrev + '/output.zip', '-d', resultsFolder, '-x', '*result-*.tar.gz'])
       subprocess.run(['rm', '-f', resultsFolderPrev + '/output.zip'])                 
#}

def eudatGetShareToken(fID): #{
   global cacheTypeGlobal
   # Checks already shared or not
   # TODO: store shareToken id with jobKey in some file, later do: oc.decline_remote_share(int(<share_id>)) to cancel shared folder at endCode or after some time later
   if os.path.isdir(lib.OC + '/' + jobKeyGlobal): # and cacheTypeGlobal is 'ipfs'
       log('Eudat shared folder is already accepted and exist on Eudat mounted folder...', 'green')              
       if os.path.isfile(lib.OC + '/' + jobKeyGlobal + '/' + jobKeyGlobal + '.tar.gz'):
           folderType = 'tar.gz'
       else:
           folderType = 'folder'
       return True
   
   global oc, shareTokenGlobal
   shareList = oc.list_open_remote_share() 

   acceptFlag      = 0 
   eudatFolderName = "" 
   log("Finding share token...")
   for i in range(len(shareList)-1, -1, -1): #{ Starts iterating from last item  to first one
      inputFolderName  = shareList[i]['name']
      inputFolderName  = inputFolderName[1:] # Removes '/' on the beginning
      inputID          = shareList[i]['id']
      inputOwner       = shareList[i]['owner']

      if (inputFolderName == jobKeyGlobal) and (inputOwner == fID): #{
         shareTokenGlobal = str(shareList[i]['share_token'])
         eudatFolderName  = str(inputFolderName)
         acceptFlag = 1
         log("Found. InputId=" + inputID + " |ShareToken: " + shareTokenGlobal)
         if cacheTypeGlobal is 'ipfs': #{
             val = oc.accept_remote_share(int(inputID));
             log('Sleeping 3 seconds for accepted folder to emerger on mounted Eudat folder...')
             time.sleep(3)

             tryCount = 0
             while True: #{
                 if tryCount is 5:
                     log('Mounted Eudat does not see shared folder\'s path.', 'red')
                     return False              
                 if os.path.isdir(lib.OC + '/' + jobKeyGlobal): # Checking is shared file emerged on mounted owncloud
                     break
                 tryCount += 1
                 log('Sleeping 10 seconds...')
                 time.sleep(10)
             #}
         #} 
         break 
      #}
   #}
   if acceptFlag == 0:
      oc.logout() 
      log("Couldn't find the shared file", 'red')
      return False
   return True
#}

def driverEudat(jobKey, index, fID, userID, eBlocBroker, web3, ocIn): #{
   global jobKeyGlobal
   global indexGlobal
   global storageIDGlobal
   global shareTokenGlobal
   global cacheTypeGlobal  
   global oc

   oc = ocIn   
   jobKeyGlobal    = jobKey  
   indexGlobal     = index 
   storageIDGlobal = '1'
   cacheTypeGlobal = 'local'
      
   log("key: "   + jobKey) 
   log("index: " + index) 

   resultsFolderPrev = lib.PROGRAM_PATH + "/" + userID + "/" + jobKey + "_" + index 
   resultsFolder     = resultsFolderPrev + '/JOB_TO_RUN' 
   
   if not eudatGetShareToken(fID): return   
   check, ipfsHash = cache(userID, resultsFolderPrev)   
   if not check: return   
   
   if not os.path.isdir(resultsFolderPrev): # If folder does not exist
      os.makedirs(resultsFolderPrev)
      os.makedirs(resultsFolder)

   if cacheTypeGlobal is 'local':
       # Untar cached tar file into local directory
       if folderType == 'tar.gz':
           subprocess.run(['tar', '-xf', lib.PROGRAM_PATH + '/' + userID + '/cache' + '/' + jobKeyGlobal + '.tar.gz', '--strip-components=1', '-C', resultsFolder])
       elif folderType == 'folder':
           subprocess.run(['rsync', '-avq', lib.PROGRAM_PATH + '/' + userID + '/cache' + '/' + jobKeyGlobal + '/', resultsFolder])              
   elif cacheTypeGlobal is 'ipfs':
       log('Reading from IPFS hash=' + ipfsHash)
       if folderType == 'tar.gz':
           subprocess.run(['tar', '-xf', '/ipfs/' + ipfsHash, '--strip-components=1', '-C', resultsFolder])
       elif eudatFolderType == 'folder':
           # Copy from cached IPFS folder into user's path           
           subprocess.run(['ipfs', 'get', ipfsHash, '-o', resultsFolder]) # cmd: ipfs get <ipfs_hash> -o .
           
   os.chdir(resultsFolder)  # 'cd' into the working path and call sbatch from there
   lib.sbatchCall(jobKeyGlobal, indexGlobal, storageIDGlobal, shareTokenGlobal, userID, resultsFolder, eBlocBroker,  web3)
#}
