#!/usr/bin/env python3

import hashlib, getpass, sys, os, time, subprocess, lib, re, pwd
from   subprocess import call
import os.path
from colored import stylize
from colored import fg
import subprocess
import glob, errno
from contractCalls.getJobInfo import getJobInfo

globals()['cacheType']         = None
globals()['folderType']        = None
globals()['index']             = None
globals()['globalCacheFolder'] = None

globals()['dataTransferIn'] = 0 # If the requested file is already cached, it stays as 0 
globals()['shareToken']    = '-1'

''' delete
def log(str_in, color=''):
   if color != '':
       print(stylize(str_in, fg(color))) 
   else:
       print(str_in)
       
   txFile = open(lib.LOG_PATH + '/transactions/clusterOut.txt', 'a') 
   txFile.write(str_in + "\n") 
   txFile.close() 

   fname = lib.LOG_PATH + '/transactions/' + jobKey + '_' + index + '_driverOutput' + '.txt'
   txFile = open(fname, 'a') 
   txFile.write(str_in + "\n") 
   txFile.close() 
'''

def isRunExistInTar(tarPath):
    try:
        FNULL = open(os.devnull, 'w')
        res = subprocess.check_output(['tar', 'ztf', tarPath, '--wildcards', '*/run.sh'], stderr=FNULL).decode('utf-8').strip()
        FNULL.close()
        if res.count('/') == 1: # Main folder should contain the 'run.sh' file
            lib.log('./run.sh exists under the parent folder', 'green')
            return True
        else:
            lib.log('Error: run.sh does not exist under the parent folder', 'red')
            return False        
    except:
        lib.log('Error_: run.sh does not exist under the parent folder', 'red')
        return False

def isTarExistsInZip(resultsFolderPrev):
    # cmd: unzip -l $resultsFolder/output.zip | grep $eudatFolderName/run.sh
    # Checks does zip contains .tar.gz file or not
    p1 = subprocess.Popen(['unzip', '-l', resultsFolderPrev + '/output.zip'], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(['grep', jobKey + '.tar.gz'], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    out = p2.communicate()[0].decode('utf-8').strip()    
    if jobKey + '.tar.gz' in out:
        globals()['folderType'] = 'tar.gz'
    else:
        globals()['folderType'] = 'folder'
    lib.log('folderType=' + globals()['folderType'])

def cache(userID, resultsFolderPrev):
    if cacheType == 'private': # First checking does is already exist under public cache directory
        globals()['globalCacheFolder'] = lib.PROGRAM_PATH +'/cache'

        if not os.path.isdir(globalCacheFolder): # If folder does not exist
            os.makedirs(globalCacheFolder)
                   
        cachedFolder  = globalCacheFolder + '/' + jobKey
        cachedTarFile = globalCacheFolder + '/' + jobKey + '.tar.gz'
        
        if not os.path.isfile(cachedTarFile):
            if os.path.isfile(cachedFolder + '/run.sh'):
                res = subprocess.check_output(['bash', lib.EBLOCPATH + '/scripts/generateMD5sum.sh', cachedFolder]).decode('utf-8').strip()
                if res == jobKey: #Checking is already downloaded folder's hash matches with the given hash                    
                    globals()['folderType'] = 'folder'
                    lib.log('Already cached under public directory...', 'green')
                    globals()['cacheType'] = 'public'
                    return True, ''
        else:
            globals()['folderType'] = 'tar.gz'
            res = subprocess.check_output(['bash', lib.EBLOCPATH + '/scripts/generateMD5sum.sh', cachedTarFile]).decode('utf-8').strip()
            if res == jobKey: # Checking is already downloaded folder's hash matches with the given hash
                lib.log('Already cached under public directory...', 'green')
                globals()['cacheType'] = 'public'
                return True, ''
    
    if cacheType == 'private' or cacheType == 'public': # Download into private directory at $HOME/.eBlocBroker/cache
        if cacheType == 'private':
            globals()['globalCacheFolder'] = lib.PROGRAM_PATH + '/' + userID + '/cache'
        elif cacheType == 'public':
            globals()['globalCacheFolder'] = lib.PROGRAM_PATH +'/cache'
        
        if not os.path.isdir(globalCacheFolder): # If folder does not exist
            os.makedirs(globalCacheFolder)
                   
        cachedFolder  = globalCacheFolder + '/' + jobKey
        cachedTarFile = globalCacheFolder + '/' + jobKey + '.tar.gz'
        
        if not os.path.isfile(cachedTarFile):
            if os.path.isfile(cachedFolder + '/run.sh'):
                res = subprocess.check_output(['bash', lib.EBLOCPATH + '/scripts/generateMD5sum.sh', cachedFolder]).decode('utf-8').strip()
                if res == jobKey: # Checking is already downloaded folder's hash matches with the given hash                    
                    globals()['folderType'] = 'folder'
                    lib.log('Already cached ...', 'green')
                    return True, ''
                else:
                    if not eudatDownloadFolder(globalCacheFolder, cachedFolder):
                        return False, ''                    
            if not eudatDownloadFolder(globalCacheFolder, cachedFolder):
                return False, ''
            if globals()['folderType'] == 'tar.gz' and not isRunExistInTar(cachedTarFile):
                lib.silentremove(cachedTarFile)
                return False, ''            
        else: # Here we already know that its tar.gz file
            globals()['folderType'] = 'tar.gz'
            res = subprocess.check_output(['bash', lib.EBLOCPATH + '/scripts/generateMD5sum.sh', cachedTarFile]).decode('utf-8').strip()
            # if globals()['folderType'] == 'tar.gz':
            #    res = subprocess.check_output(['bash', lib.EBLOCPATH + '/scripts/generateMD5sum.sh', cachedTarFile]).decode('utf-8').strip()
            # elif globals()['folderType'] == 'folder':
            #    res = subprocess.check_output(['bash', lib.EBLOCPATH + '/scripts/generateMD5sum.sh', cachedFolder]).decode('utf-8').strip()
            if res == jobKey: #Checking is already downloaded folder's hash matches with the given hash
                lib.log('Already cached ...', 'green')
                return True, ''
            else:
                if not eudatDownloadFolder(globalCacheFolder, cachedFolder):
                    return False, ''
    elif cacheType == 'ipfs':
        lib.log('Adding from owncloud mount point into IPFS...', 'blue')
        tarFile = lib.OWN_CLOUD_PATH + '/' + jobKey + '/' + jobKey + '.tar.gz'        
        if os.path.isfile(tarFile):            
            globals()['folderType'] = 'tar.gz'
            ipfsHash = subprocess.check_output(['ipfs', 'add', tarFile]).decode('utf-8').strip() #TODO: add try catch, try few times if error generated
        else:
            globals()['folderType'] = 'folder'
            ipfsHash = subprocess.check_output(['ipfs', 'add', '-r', lib.OWN_CLOUD_PATH + '/' + jobKey]).decode('utf-8').strip()            
            ipfsHash = ipfsHash.splitlines()
            ipfsHash = ipfsHash[int(len(ipfsHash) - 1)] # Last line of ipfs hash output is obtained which has the root folder's hash
        return True, ipfsHash.split()[1]
    return True, ''

# Assume job is sent as .tar.gz file
def eudatDownloadFolder(resultsFolderPrev, resultsFolder):
   # cmd: wget --continue -4 -o /dev/stdout https://b2drop.eudat.eu/s/$shareToken/download --output-document=$resultsFolderPrev/output.zip
    lib.log('Downloading output.zip -> ' + resultsFolderPrev + '/output.zip')
    for attempt in range(5):
        try:
            ret = subprocess.check_output(['wget', '--continue', '-4', '-o', '/dev/stdout', 'https://b2drop.eudat.eu/s/' + shareToken +
                                           '/download', '--output-document=' + resultsFolderPrev + '/output.zip']).decode('utf-8')
        except Exception as e:
            lib.log('Failed to download eudat file: '+ str(e), 'red')
            time.sleep(5)
        else:
            break;
    else:
        return False
    
    result = re.search('Length: (.*) \(', ret) # https://stackoverflow.com/a/6986163/2402577
    if result is not None: # from wget output
        globals()['dataTransferIn'] = int(result.group(1)) * 0.000001 # Downloaded file size in MBs
    else: # from downloaded files size in bytes
        # p1 = subprocess.Popen(['du', '-b', resultsFolderPrev + '/output.zip'], stdout=subprocess.PIPE)
        p1 = subprocess.Popen(['ls', '-ln', resultsFolderPrev + '/output.zip'], stdout=subprocess.PIPE)
        #-----------
        # p2 = subprocess.Popen(['awk', '{print $1}'], stdin=p1.stdout, stdout=subprocess.PIPE)
        p2 = subprocess.Popen(['awk', '{print $5}'], stdin=p1.stdout, stdout=subprocess.PIPE)
        p1.stdout.close()
        #-----------
        out = p2.communicate()[0].decode('utf-8').strip() # Retunrs downloaded files size in bytes       
        # print(out)
        globals()['dataTransferIn'] = int(out) * 0.000001 # Downloaded file size in MBs
    lib.log('dataTransferIn=' + str(dataTransferIn) + ' MB', 'green')
   
    if "ERROR 404: Not Found" in ret:
        lib.log(ret, 'red') 
        lib.log('File not found The specified document has not been found on the server.', 'red') 
        # TODO: since folder does not exist, do complete refund to the user.
        return False
    
    lib.log(ret) 
    isTarExistsInZip(resultsFolderPrev)   
    time.sleep(0.25) 
    if os.path.isfile(resultsFolderPrev + '/output.zip'):
        if globals()['folderType'] == 'tar.gz':           
            subprocess.run(['unzip', '-jo', resultsFolderPrev + '/output.zip', '-d', resultsFolderPrev, '-x', '*result-*.tar.gz'])
        else:
            subprocess.run(['unzip', '-o', resultsFolderPrev + '/output.zip', '-d', resultsFolder, '-x', '*result-*.tar.gz'])
        lib.silentremove(resultsFolderPrev + '/output.zip')    
    return True

# Checks already shared or not
def eudatGetShareToken(fID, userID):
   saveShareToken = lib.PROGRAM_PATH + '/' + userID + '/cache' + '/' + jobKey + '_shareToken.txt'
   # TODO: store shareToken id with jobKey in some file, later do: oc.decline_remote_share(int(<share_id>)) to cancel shared folder at endCode or after some time later
   if cacheType == 'ipfs' and os.path.isdir(lib.OWN_CLOUD_PATH + '/' + jobKey):
       lib.log('Eudat shared folder is already accepted and exist on Eudat mounted folder...', 'green')              
       if os.path.isfile(lib.OWN_CLOUD_PATH + '/' + jobKey + '/' + jobKey + '.tar.gz'):
           globals()['folderType'] = 'tar.gz'
       else:
           globals()['folderType'] = 'folder'

       if os.path.isfile(saveShareToken):
           with open(saveShareToken, 'r') as content_file:
               content = content_file.read()                  
               if content:
                   globals()['shareToken'] = content
               else:
                   content = None                     
       lib.log("ShareToken=" + shareToken)           
       return True

   for attempt in range(5):
       try:
           shareList = oc.list_open_remote_share()
       except Exception as e:
            lib.log('Error: Failed to list_open_remote_share eudat: '+ str(e), 'red')
            time.sleep(1)
       else:
           break
   else:
       return False       
   
   acceptFlag      = 0 
   eudatFolderName = ""
   lib.log("Finding share token...")
   for i in range(len(shareList)-1, -1, -1): # Starts iterating from last item  to first one
      inputFolderName  = shareList[i]['name']
      inputFolderName  = inputFolderName[1:] # Removes '/' on the beginning
      inputID          = shareList[i]['id']
      inputOwner       = shareList[i]['owner']      
      if inputFolderName == jobKey and inputOwner == fID:
         globals()['shareToken'] = str(shareList[i]['share_token'])
         eudatFolderName  = str(inputFolderName)
         acceptFlag       = 1
         lib.log("Found. InputId=" + inputID + " |ShareToken=" + shareToken)

         saveDirShareToken = lib.PROGRAM_PATH + '/' + userID + '/cache'
         if not os.path.isdir(saveDirShareToken):
             lib.log(saveDirShareToken + ' does not exist', 'red')
             return
         
         with open(saveShareToken, 'w') as the_file:  # TODO check is file exist if not return
             the_file.write(shareToken)                  
         
         if cacheType == 'ipfs':
             val = oc.accept_remote_share(int(inputID));
             lib.log('Sleeping 3 seconds for accepted folder to emerge on the mounted Eudat folder...')
             time.sleep(3)
             tryCount = 0
             while True:
                 if tryCount is 5:
                     lib.log("Mounted Eudat does not see shared folder's path.", 'red')
                     return False              
                 if os.path.isdir(lib.OWN_CLOUD_PATH + '/' + jobKey): # Checking is shared file emerged on mounted owncloud
                     break
                 tryCount += 1
                 lib.log('Sleeping 10 seconds...')
                 time.sleep(10)
         break     
   if acceptFlag == 0:
      oc.logout() 
      lib.log("Error: Couldn't find the shared file", 'red')
      return False
   return True
                               
def driverEudat(jobKey_, index_, fID, userID, sourceCodeHash, cacheType_, gasStorageHour, eBlocBroker, web3, oc_):
    storageID = '1'   
    globals()['jobKey']    = jobKey_
    globals()['oc']        = oc_    
    globals()['index']     = index_    
    globals()['cacheType'] = lib.cacheType.reverse_mapping[cacheType_]               
    
    lib.log('jobKey=' + jobKey) 
    lib.log('index=' + index)
    lib.log('fID=' + fID)
    lib.log('cacheType=' + cacheType)
    
    resultsFolderPrev = lib.PROGRAM_PATH + "/" + userID + "/" + jobKey + "_" + index 
    resultsFolder     = resultsFolderPrev + '/JOB_TO_RUN' 
   
    if not eudatGetShareToken(fID, userID): return
    
    if cacheType != 'none':
        check, ipfsHash = cache(userID, resultsFolderPrev)
        
    if not check: return   
    
    if not os.path.isdir(resultsFolderPrev): # If folder does not exist
        os.makedirs(resultsFolderPrev)
        os.makedirs(resultsFolder)

    if cacheType == 'private' or cacheType == 'public':
        '''
        if cacheType == 'private':
            globals()['globalCacheFolder'] = lib.PROGRAM_PATH + '/' + userID + '/cache'
        elif cacheType == 'public':
            globals()['globalCacheFolder'] = lib.PROGRAM_PATH +'/cache'
        '''
        # Untar cached tar file into private directory
        if globals()['folderType'] == 'tar.gz':
            subprocess.run(['tar', '-xf', globalCacheFolder + '/' + jobKey + '.tar.gz', '--strip-components=1', '-C', resultsFolder])
        elif globals()['folderType'] == 'folder':
            subprocess.run(['rsync', '-avq', '--partial-dir', '--omit-dir-times', globalCacheFolder + '/' + jobKey + '/', resultsFolder])
    elif cacheType == 'ipfs':
        lib.log('Reading from IPFS hash=' + ipfsHash)
        if globals()['folderType'] == 'tar.gz':
            subprocess.run(['tar', '-xf', '/ipfs/' + ipfsHash, '--strip-components=1', '-C', resultsFolder])
        elif eudatFolderType == 'folder':
            # Copy from cached IPFS folder into user's path           
            subprocess.run(['ipfs', 'get', ipfsHash, '-o', resultsFolder]) # cmd: ipfs get <ipfs_hash> -o .           

    try:
        lib.log('dataTransferIn: ' + str(dataTransferIn))
        lib.sbatchCall(jobKey, index, storageID, shareToken, userID,
                       resultsFolder, resultsFolderPrev, dataTransferIn,
                       gasStorageHour, sourceCodeHash, eBlocBroker,  web3)
        time.sleep(1)
    except Exception as e:
        lib.log('Failed to sbatch call: '+ str(e), 'red')
        return False    
