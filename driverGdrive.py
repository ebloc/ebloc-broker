#!/usr/bin/env python3

import owncloud, hashlib, getpass, sys, os, time, subprocess, lib, re, glob, errno, json
from datetime   import datetime, timedelta
from subprocess import call
from colored    import stylize
from colored    import fg
from contractCalls.getJobInfo      import getJobInfo
from contractCalls.getProviderInfo import getProviderInfo

def log(my_string, color=''): 
    if color != '':
        print(stylize(my_string, fg(color))) 
    else:
        print(my_string)

    file_name = lib.LOG_PATH + '/transactions/providerOut.txt'
    f = open(file_name, 'a') 
    f.write(my_string + "\n") 
    f.close()
   
    file_name = lib.LOG_PATH + '/transactions/' + jobKey + '_' + str(index) + '_driverOutput' + '.txt'
    f = open(file_name, 'a') 
    f.write(my_string + "\n") 
    f.close() 
    
def cache(requester, resultsFolderPrev, folderName, sourceCodeHash, folderType, key, jobKeyFlag):
    '''
    if jobKeyFlag:
        if not os.path.isfile(globalCachePath + '/' + folderName + '/run.sh'):
            return False, None
    '''
    
    if cacheType == lib.CacheType.PRIVATE.value: # First checking does is already exist under public cache directory
        globals()['globalCachePath'] = lib.PROGRAM_PATH + '/' + requester + '/cache'
        if not os.path.isdir(globalCachePath): # If folder does not exist
            os.makedirs(globalCachePath)
            
        cachedTarFile = globalCachePath + '/' + folderName        
        if folderType == 'gzip':
           if os.path.isfile(cachedTarFile):
              res = subprocess.check_output(['bash', lib.EBLOCPATH + '/scripts/generateMD5sum.sh', cachedTarFile]).decode('utf-8').strip()

              if res != md5sum_dict[key]:
                  log("File's md5sum does not match with its orignal md5sum value", 'red')
                  return False, None
              
              if res == sourceCodeHash: #Checking is already downloaded folder's hash matches with the given hash
                 log(folderName + ' is already cached within private cache directory...', 'green')
                 globals()['cacheType'] = lib.CacheType.PRIVATE.value
                 return True, None
        elif folderType == 'folder':
           if os.path.isfile(globalCachePath + '/' + folderName + '/' + sourceCodeHash + '.tar.gz'):
               tarFile = globalCachePath + '/' + folderName + '/' + sourceCodeHash + '.tar.gz'
               res = subprocess.check_output(['bash', lib.EBLOCPATH + '/scripts/generateMD5sum.sh', tarFile]).decode('utf-8').strip()
           else:
               res = subprocess.check_output(['bash', lib.EBLOCPATH + '/scripts/generateMD5sum.sh', globalCachePath + '/' + folderName]).decode('utf-8').strip()
               
           if res == sourceCodeHash: #Checking is already downloaded folder's hash matches with the given hash
               log(folderName + ' is already cached within the private cache directory...', 'green')
               globals()['cacheType'] = lib.CacheType.PRIVATE.value
               return True, None
             
    # if cacheType == lib.CacheType.PRIVATE.value  or
    if cacheType == lib.CacheType.PUBLIC.value:
        globals()['globalCachePath'] = lib.PROGRAM_PATH + '/cache'        
        if not os.path.isdir(globalCachePath): # If folder does not exist
            os.makedirs(globalCachePath)
            
        cachedTarFile = globalCachePath + '/' + folderName        
        if folderType == 'gzip':
           if not os.path.isfile(cachedTarFile):
              if not gdriveDownloadFolder(globalCachePath, folderName, folderType, key):
                  return False, None
              
              if jobKeyFlag and not lib.isRunExistInTar(cachedTarFile):
                 lib.silentremove(cachedTarFile)
                 return False, None
           else:
              res = subprocess.check_output(['bash', lib.EBLOCPATH + '/scripts/generateMD5sum.sh', cachedTarFile]).decode('utf-8').strip()
              if res == sourceCodeHash: #Checking is already downloaded folder's hash matches with the given hash
                 log(folderName + ' is already cached within public cache directory...', 'green')
              else:
                 if not gdriveDownloadFolder(globalCachePath, folderName, folderType, key):
                     return False, None
        elif folderType == 'folder':
           if os.path.isfile(globalCachePath + '/' + folderName + '/' + sourceCodeHash + '.tar.gz'):
              tarFile = globalCachePath + '/' + folderName + '/' + sourceCodeHash + '.tar.gz'
              res = subprocess.check_output(['bash', lib.EBLOCPATH + '/scripts/generateMD5sum.sh', tarFile]).decode('utf-8').strip()
              if res == sourceCodeHash: #Checking is already downloaded folder's hash matches with the given hash
                  log(folderName + ' is already cached within public cache directory...', 'green')
              else:                 
                 if not gdriveDownloadFolder(globalCachePath, folderName, folderType, key):
                     return False, None
                 #os.rename(globalCachePath + '/' + folderName, globalCachePath + '/' + jobKey)
           else:                 
              if not gdriveDownloadFolder(globalCachePath, folderName, folderType, key):
                  return False, None
              # os.rename(globalCachePath + '/' + folderName, globalCachePath + '/' + jobKey)              
    elif cacheType == lib.CacheType.IPFS.value:
        log('Adding from google drive mount point into IPFS...', 'blue')
        if folderType == 'gzip':
           tarFile = lib.GDRIVE_CLOUD_PATH + '/.shared/' + folderName           
           if not os.path.isfile(tarFile):
              # TODO: It takes 3-5 minutes for shared folder/file to show up on the .shared folder
              log('Requested file does not exit on mounted folder. PATH=' + tarFile, 'red')
              return False, None
           ipfsHash = subprocess.check_output(['ipfs', 'add', tarFile]).decode('utf-8').strip()              
        elif folderType == 'folder':
            folderPath = lib.GDRIVE_CLOUD_PATH + '/.shared/' + folderName
            if not os.path.isdir(folderPath):
               log('Requested folder does not exit on mounted folder. PATH=' + folderPath, 'red')
               return False, None
           
            ipfsHash = subprocess.check_output(['ipfs', 'add', '-r', folderPath]).decode('utf-8').strip()            
            ipfsHash = ipfsHash.splitlines()
            ipfsHash = ipfsHash[int(len(ipfsHash) - 1)] # Last line of ipfs hash output is obtained which has the root folder's hash        
        return True, ipfsHash.split()[1]
    
    return True, None

def gdriveDownloadFolder(resultsFolderPrev, folderName, folderType, key) -> bool:        
    if folderType == 'folder':
        # cmd: gdrive download --recursive $key --force --path $resultsFolderPrev  # Gets the source  %TODOTODO
        status, res = lib.subprocessCallAttempt(['gdrive', 'download', '--recursive', key, '--force', '--path', resultsFolderPrev], 10)
        if not status:
            return False
        
        if not os.path.isdir(resultsFolderPrev + '/' + folderName): # Check before move operation
            log('Folder is not downloaded successfully.', 'red')
            return False
        else:
            p1 = subprocess.Popen(['du', '-sb', resultsFolderPrev + '/' + folderName], stdout=subprocess.PIPE)
            p2 = subprocess.Popen(['awk', '{print $1}'], stdin=p1.stdout, stdout=subprocess.PIPE)
            p1.stdout.close()

            globals()['dataTransferIn'] = p2.communicate()[0].decode('utf-8').strip() # Retunrs downloaded files size in bytes
            globals()['dataTransferIn'] = lib.convertByteToMB(globals()['dataTransferIn'])
            log('dataTransferIn=' + str(dataTransferIn) + ' MB | Rounded=' + str(int(dataTransferIn)) + ' MB', 'green')    
    else:
        # cmd: gdrive download $key --force --path $resultsFolderPrev
        status, res = lib.subprocessCallAttempt(['gdrive', 'download', key, '--force', '--path', resultsFolderPrev], 10)
        if not status:
            return False

        if not os.path.isfile(resultsFolderPrev + '/' + folderName):
            log('File is not downloaded successfully.', 'red')
            return False
        else:
            p1 = subprocess.Popen(['ls', '-ln', resultsFolderPrev + '/' + folderName], stdout=subprocess.PIPE)
            p2 = subprocess.Popen(['awk', '{print $5}'], stdin=p1.stdout, stdout=subprocess.PIPE)
            p1.stdout.close()
            globals()['dataTransferIn'] = p2.communicate()[0].decode('utf-8').strip() # Returns downloaded files size in bytes
            globals()['dataTransferIn'] = lib.convertByteToMB(globals()['dataTransferIn'])
            log('dataTransferIn=' + str(dataTransferIn) + ' MB | Rounded=' + str(int(dataTransferIn)) + ' MB', 'green')
            
    return True

def getData(key, requester, resultsFolderPrev, resultsFolder, jobKeyFlag=False):
    #cmd: gdrive info $key -c $GDRIVE_METADATA # stored for both pipes otherwise its read and lost
    status, gdriveInfo = lib.subprocessCallAttempt(['gdrive', 'info', '--bytes', key, '-c', lib.GDRIVE_METADATA], 10)
    if not status:
        return False

    mimeType       = lib.getGdriveFileInfo(gdriveInfo, 'Mime')    
    folderName     = lib.getGdriveFileInfo(gdriveInfo, 'Name')    
    log('mimeType='   + mimeType)
    log('folderName=' + folderName)

    if jobKeyFlag:
        # key for the sourceCode tar.gz file is obtained
        status, _size, globals()['jobKey_list'], key = lib.gdriveSize(key, mimeType, folderName, gdriveInfo, resultsFolderPrev, sourceCodeHash_list, shouldAlreadyCached)
        if not status:
            return False        
        
        log('size=' + str(_size) + ' MB')
        status, gdriveInfo = lib.subprocessCallAttempt(['gdrive', 'info', '--bytes', key, '-c', lib.GDRIVE_METADATA], 10)
        if not status: return False
        mimeType       = lib.getGdriveFileInfo(gdriveInfo, 'Mime')    
        folderName     = lib.getGdriveFileInfo(gdriveInfo, 'Name')
        # TODO: sizes compare if exceeds retrun False

    sourceCodeHash = folderName.replace('.tar.gz','') # folder is already stored by its sourceCodeHash
    log('mimeType='   + mimeType)
    log('folderName=' + folderName)

    if 'gzip' in mimeType:
        sourceCodeHash = lib.getMd5sum(gdriveInfo) # if it is gzip obtained from the {gdrive info key}
        globals()['md5sum_dict'][key] = sourceCodeHash
        log('Md5sum=' + md5sum_dict[key])
                    
    if cacheType == lib.CacheType.PRIVATE.value or cacheType == lib.CacheType.PUBLIC.value:
        if 'folder' in mimeType: # Recieved job is in folder format
            if cacheType != lib.CacheType.NONE.value: 
                status, ipfsHash = cache(requester, resultsFolderPrev, folderName, sourceCodeHash, 'folder', key, jobKeyFlag)                
            if not status:
                return False

            command = ['rsync', '-avq', '--partial-dir', '--omit-dir-times', globalCachePath + '/' + folderName + '/', resultsFolder]
            status, result = lib.executeShellCommand(command, None, True)
            if os.path.isfile(resultsFolder + '/' + folderName + '.tar.gz'):
                command = ['tar', '-xf', resultsFolder + '/' + folderName + '.tar.gz', '--strip-components=1', '-C', resultsFolder]
                status, result = lib.executeShellCommand(command, None, True)
                lib.silentremove(resultsFolder + '/' + folderName + '.tar.gz')            
        elif 'gzip' in mimeType: # Recieved job is in folder tar.gz
            if cacheType != lib.CacheType.NONE.value:
                status, ipfsHash = cache(requester, resultsFolderPrev, folderName, sourceCodeHash, 'gzip', key, jobKeyFlag)             
            if not status:
                return False

            command = ['tar', '-xf', globalCachePath + '/' + folderName, '--strip-components=1', '-C', resultsFolder]
            status, result = lib.executeShellCommand(command, None, True)
        else:
            return False
        '''    
        elif 'zip' in mimeType: # Recieved job is in zip format
            if cacheType != lib.CacheType.NONE.value: 
                status, ipfsHash = cache(requester, resultsFolderPrev, folderName, sourceCodeHash, 'zip', key, jobKeyFlag)             
            if not status:
                return False
         
            # cmd: unzip -o $resultsFolderPrev/$folderName -d $resultsFolder
            command = ['unzip', '-o', resultsFolderPrev + '/' + folderName, '-d', resultsFolder]
            status, result = lib.executeShellCommand(command, None, True)
            lib.silentremove(resultsFolderPrev + '/' + folderName)
        '''
    ''' Gdrive => IPFS no need.
    elif cacheType == lib.CacheType.IPFS.value:
        if 'folder' in mimeType:
            if cacheType != lib.CacheType.NONE.value:
                status, ipfsHash = cache(requester, resultsFolderPrev, folderName, sourceCodeHash, 'folder', key, jobKeyFlag)
            if not status:
                return False

            if ipfsHash is None:
                log('E: Requested IPFS hash does not exist.')
                return False

         
            log('Reading from IPFS hash=' + ipfsHash)
            # Copy from cached IPFS folder into user's path
            command = ['ipfs', 'get', ipfsHash, '-o', resultsFolder]
            status, result = lib.executeShellCommand(command, None, True)
        elif 'gzip' in mimeType:
            if cacheType != lib.CacheType.NONE.value:
                status, ipfsHash = cache(requester, resultsFolderPrev, folderName, sourceCodeHash, 'gzip', key, jobKeyFlag)
            if not status:
                return False
         
            log('Reading from IPFS hash=' + ipfsHash)
            command = ['tar', '-xf', '/ipfs/' + ipfsHash, '--strip-components=1', '-C', resultsFolder]
            status, result = lib.executeShellCommand(command, None, True)
    '''
    ''' delete
    data = None
    if jobKeyFlag:
        file_path = resultsFolder + '/' + 'dataFiles.json'
        if os.path.exists(file_path):
            with open(file_path) as f:
                data = json.load(f)
                for (k, v) in data.items():
                    globals()['jobKey_list'].append(str(v))
                
    return data
    '''
    
def driverGdrive(loggedJob, jobInfo, requester, shouldAlreadyCached, eBlocBroker, w3) -> bool:
    status, providerInfo = getProviderInfo(loggedJob.args['provider'])
    globals()['fID']            = providerInfo['fID']    
    globals()['jobKey']         = loggedJob.args['jobKey']
    globals()['index']          = loggedJob.args['index']
    globals()['storageID']      = loggedJob.args['storageID']
    globals()['cacheType'] = loggedJob.args['cacheType']
    
    globals()['shouldAlreadyCached'] = shouldAlreadyCached    
    globals()['dataTransferIn']      = jobInfo[0]['dataTransferIn']        
    globals()['sourceCodeHash_list'] = loggedJob.args['sourceCodeHash']
    globals()['sourceCodeHashText_list'] = []
    globals()['jobKey_list'] = []
    globals()['md5sum_dict'] = {}        
    globals()['dataTransferIn'] = 0 # if the requested file is already cached, it stays as 0
       
    resultsFolderPrev = lib.PROGRAM_PATH + "/" + requester + "/" + jobKey + "_" + str(index)
    resultsFolder     = resultsFolderPrev + '/JOB_TO_RUN'    
    
    if not os.path.isdir(resultsFolderPrev): # If folder does not exist
        os.makedirs(resultsFolderPrev)
        os.makedirs(resultsFolder)

    getData(jobKey, requester, resultsFolderPrev, resultsFolder, True)
    for i in range(0, len(jobKey_list)):
        key = jobKey_list[i]
        getData(key, requester, resultsFolderPrev, resultsFolder)

    sys.exit() # TODO: delete
    shareToken = "-1" # fixed value for gdrive
    status = lib.sbatchCall(loggedJob, shareToken, requester, resultsFolder, resultsFolderPrev, dataTransferIn, sourceCodeHash_list, jobInfo, eBlocBroker,  w3)
