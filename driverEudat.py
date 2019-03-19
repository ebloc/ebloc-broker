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

def isRunExistInTar(tarPath):
    try:
        FNULL = open(os.devnull, 'w')
        res = subprocess.check_output(['tar', 'ztf', tarPath, '--wildcards', '*/run.sh'], stderr=FNULL).decode('utf-8').strip()
        FNULL.close()
        if res.count('/') == 1: # Main folder should contain the 'run.sh' file
            log('./run.sh exists under the parent folder', 'green')
            return True
        else:
            log('Error: run.sh does not exist under the parent folder', 'red')
            return False        
    except:
        log('Error_: run.sh does not exist under the parent folder', 'red')
        return False

def isTarExistsInZip(resultsFolderPrev):
    # cmd: unzip -l $resultsFolder/output.zip | grep $eudatFolderName/run.sh
    # Checks does zip contains .tar.gz file or not
    p1 = subprocess.Popen(['unzip', '-l', resultsFolderPrev + '/output.zip'], stdout=subprocess.PIPE)
    #-----------
    p2 = subprocess.Popen(['grep', globals()['jobKey'] + '.tar.gz'], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    #-----------
    out = p2.communicate()[0].decode('utf-8').strip()    
    if globals()['jobKey'] + '.tar.gz' in out:
        globals()['folderType'] = 'tar.gz'
    else:
        globals()['folderType'] = 'folder'
    log('folderType=' + globals()['folderType'])

def cache(userID, resultsFolderPrev):
    if globals()['cacheType'] == 'private': # First checking does is already exist under public cache directory
        globals()['globalCacheFolder'] = lib.PROGRAM_PATH +'/cache'

        if not os.path.isdir(globals()['globalCacheFolder']): # If folder does not exist
            os.makedirs(globals()['globalCacheFolder'])
                   
        cachedFolder  = globals()['globalCacheFolder'] + '/' + globals()['jobKey']
        cachedTarFile = globals()['globalCacheFolder'] + '/' + globals()['jobKey'] + '.tar.gz'
        
        if not os.path.isfile(cachedTarFile):
            if os.path.isfile(cachedFolder + '/run.sh'):
                res = subprocess.check_output(['bash', lib.EBLOCPATH + '/scripts/generateMD5sum.sh', cachedFolder]).decode('utf-8').strip()
                if res == globals()['jobKey']: #Checking is already downloaded folder's hash matches with the given hash                    
                    globals()['folderType'] = 'folder'
                    log('Already cached under public directory...', 'green')
                    globals()['cacheType'] = 'public'
                    return True, ''
        else:
            globals()['folderType'] = 'tar.gz'
            res = subprocess.check_output(['bash', lib.EBLOCPATH + '/scripts/generateMD5sum.sh', cachedTarFile]).decode('utf-8').strip()
            if res == globals()['jobKey']: # Checking is already downloaded folder's hash matches with the given hash
                log('Already cached under public directory...', 'green')
                globals()['cacheType'] = 'public'
                return True, ''
    
    if globals()['cacheType'] == 'private' or globals()['cacheType'] == 'public': # Download into private directory at $HOME/.eBlocBroker/cache
        if globals()['cacheType'] is 'private':
            globals()['globalCacheFolder'] = lib.PROGRAM_PATH + '/' + userID + '/cache'
        elif globals()['cacheType'] is 'public':
            globals()['globalCacheFolder'] = lib.PROGRAM_PATH +'/cache'
        
        if not os.path.isdir(globals()['globalCacheFolder']): # If folder does not exist
            os.makedirs(globals()['globalCacheFolder'])
                   
        cachedFolder  = globals()['globalCacheFolder'] + '/' + globals()['jobKey']
        cachedTarFile = globals()['globalCacheFolder'] + '/' + globals()['jobKey'] + '.tar.gz'
        
        if not os.path.isfile(cachedTarFile):
            if os.path.isfile(cachedFolder + '/run.sh'):
                res = subprocess.check_output(['bash', lib.EBLOCPATH + '/scripts/generateMD5sum.sh', cachedFolder]).decode('utf-8').strip()
                if res == globals()['jobKey']: # Checking is already downloaded folder's hash matches with the given hash                    
                    globals()['folderType'] = 'folder'
                    log('Already cached ...', 'green')
                    return True, ''
                else:
                    if not eudatDownloadFolder(globals()['globalCacheFolder'], cachedFolder):
                        return False, ''                    
            if not eudatDownloadFolder(globals()['globalCacheFolder'], cachedFolder):
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
            if res == globals()['jobKey']: #Checking is already downloaded folder's hash matches with the given hash
                log('Already cached ...', 'green')
                return True, ''
            else:
                if not eudatDownloadFolder(globals()['globalCacheFolder'], cachedFolder):
                    return False, ''
    elif globals()['cacheType'] == 'ipfs':
        log('Adding from owncloud mount point into IPFS...', 'blue')
        tarFile = lib.OWN_CLOUD_PATH + '/' + globals()['jobKey'] + '/' + globals()['jobKey'] + '.tar.gz'        
        if os.path.isfile(tarFile):            
            globals()['folderType'] = 'tar.gz'
            ipfsHash = subprocess.check_output(['ipfs', 'add', tarFile]).decode('utf-8').strip() #TODO: add try catch, try few times if error generated
        else:
            globals()['folderType'] = 'folder'
            ipfsHash = subprocess.check_output(['ipfs', 'add', '-r', lib.OWN_CLOUD_PATH + '/' + globals()['jobKey']]).decode('utf-8').strip()            
            ipfsHash = ipfsHash.splitlines()
            ipfsHash = ipfsHash[int(len(ipfsHash) - 1)] # Last line of ipfs hash output is obtained which has the root folder's hash
        return True, ipfsHash.split()[1]
    return True, ''

# Assume job is sent as .tar.gz file
def eudatDownloadFolder(resultsFolderPrev, resultsFolder):
   # cmd: wget --continue -4 -o /dev/stdout https://b2drop.eudat.eu/s/$shareToken/download --output-document=$resultsFolderPrev/output.zip
    log('Downloading output.zip -> ' + resultsFolderPrev + '/output.zip')
    for attempt in range(5):
        try:
            ret = subprocess.check_output(['wget', '--continue', '-4', '-o', '/dev/stdout', 'https://b2drop.eudat.eu/s/' + globals()['shareToken'] +
                                           '/download', '--output-document=' + resultsFolderPrev + '/output.zip']).decode('utf-8')
        except Exception as e:
            log('Failed to download eudat file: '+ str(e), 'red')
            time.sleep(5)
        else:
            break;
    else:
        return
    
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
    log('dataTransferIn=' + str(globals()['dataTransferIn']) + ' MB', 'green')
   
    if "ERROR 404: Not Found" in ret:
        log(ret, 'red') 
        log('File not found The specified document has not been found on the server.', 'red') 
        # TODO: since folder does not exist, do complete refund to the user.
        return False
    
    log(ret) 
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
   saveShareToken = lib.PROGRAM_PATH + '/' + userID + '/cache' + '/' + globals()['jobKey'] + '_shareToken.txt'
   # TODO: store shareToken id with jobKey in some file, later do: globals()['oc'].decline_remote_share(int(<share_id>)) to cancel shared folder at endCode or after some time later
   if globals()['cacheType'] == 'ipfs' and os.path.isdir(lib.OWN_CLOUD_PATH + '/' + globals()['jobKey']):
       log('Eudat shared folder is already accepted and exist on Eudat mounted folder...', 'green')              
       if os.path.isfile(lib.OWN_CLOUD_PATH + '/' + globals()['jobKey'] + '/' + globals()['jobKey'] + '.tar.gz'):
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
       log("ShareToken=" + globals()['shareToken'])           
       return True

   shareList = globals()['oc'].list_open_remote_share() 
   acceptFlag      = 0 
   eudatFolderName = ""
   log("Finding share token...")
   for i in range(len(shareList)-1, -1, -1): # Starts iterating from last item  to first one
      inputFolderName  = shareList[i]['name']
      inputFolderName  = inputFolderName[1:] # Removes '/' on the beginning
      inputID          = shareList[i]['id']
      inputOwner       = shareList[i]['owner']      
      if inputFolderName == globals()['jobKey'] and inputOwner == fID:
         globals()['shareToken'] = str(shareList[i]['share_token'])
         eudatFolderName  = str(inputFolderName)
         acceptFlag       = 1
         log("Found. InputId=" + inputID + " |ShareToken=" + globals()['shareToken'])

         saveDirShareToken = lib.PROGRAM_PATH + '/' + userID + '/cache'
         if not os.path.isdir(saveDirShareToken):
             log(saveDirShareToken + ' does not exist', 'red')
             return
         
         with open(saveShareToken, 'w') as the_file:  # TODO check is file exist if not return
             the_file.write(globals()['shareToken'])                  
         
         if globals()['cacheType'] is 'ipfs':
             val = globals()['oc'].accept_remote_share(int(inputID));
             log('Sleeping 3 seconds for accepted folder to emerge on the mounted Eudat folder...')
             time.sleep(3)
             tryCount = 0
             while True:
                 if tryCount is 5:
                     log('Mounted Eudat does not see shared folder\'s path.', 'red')
                     return False              
                 if os.path.isdir(lib.OWN_CLOUD_PATH + '/' + globals()['jobKey']): # Checking is shared file emerged on mounted owncloud
                     break
                 tryCount += 1
                 log('Sleeping 10 seconds...')
                 time.sleep(10)
         break     
   if acceptFlag == 0:
      globals()['oc'].logout() 
      log("Error: Couldn't find the shared file", 'red')
      return False
   return True

def driverEudat(jobKey, index, fID, userID, cacheType, eBlocBroker, web3, oc):
    storageID = '1'   
    globals()['jobKey']    = jobKey
    globals()['oc']        = oc    
    globals()['index']     = index    
    globals()['cacheType'] = lib.cacheType.reverse_mapping[cacheType]               
    
    log("jobKey=" + jobKey) 
    log("index="  + index)
    log("fID="  + fID)
    log("cacheType=" + globals()['cacheType'])
    
    resultsFolderPrev = lib.PROGRAM_PATH + "/" + userID + "/" + jobKey + "_" + index 
    resultsFolder     = resultsFolderPrev + '/JOB_TO_RUN' 
   
    if not eudatGetShareToken(fID, userID): return
    
    if globals()['cacheType'] != 'none':
        check, ipfsHash = cache(userID, resultsFolderPrev)
        
    if not check: return   
    
    if not os.path.isdir(resultsFolderPrev): # If folder does not exist
        os.makedirs(resultsFolderPrev)
        os.makedirs(resultsFolder)

    if globals()['cacheType'] == 'private' or globals()['cacheType'] == 'public':
        '''
        if globals()['cacheType'] is 'private':
            globals()['globalCacheFolder'] = lib.PROGRAM_PATH + '/' + userID + '/cache'
        elif globals()['cacheType'] is 'public':
            globals()['globalCacheFolder'] = lib.PROGRAM_PATH +'/cache'
        '''
        # Untar cached tar file into private directory
        if globals()['folderType'] == 'tar.gz':
            subprocess.run(['tar', '-xf', globals()['globalCacheFolder'] + '/' + globals()['jobKey'] + '.tar.gz', '--strip-components=1', '-C', resultsFolder])
        elif globals()['folderType'] == 'folder':
            subprocess.run(['rsync', '-avq', '--partial-dir', '--omit-dir-times', globals()['globalCacheFolder'] + '/' + globals()['jobKey'] + '/', resultsFolder])
    elif globals()['cacheType'] == 'ipfs':
        log('Reading from IPFS hash=' + ipfsHash)
        if globals()['folderType'] == 'tar.gz':
            subprocess.run(['tar', '-xf', '/ipfs/' + ipfsHash, '--strip-components=1', '-C', resultsFolder])
        elif eudatFolderType == 'folder':
            # Copy from cached IPFS folder into user's path           
            subprocess.run(['ipfs', 'get', ipfsHash, '-o', resultsFolder]) # cmd: ipfs get <ipfs_hash> -o .           
    # os.chdir(resultsFolder)  # 'cd' into the working path and call sbatch from there    TODO: delete
    try:
        lib.sbatchCall(globals()['jobKey'], globals()['index'], storageID, globals()['shareToken'], userID,
                       resultsFolder, resultsFolderPrev, globals()['dataTransferIn'], eBlocBroker,  web3)
        time.sleep(1)
    except Exception as e:
        log('Failed to sbatch call: '+ str(e), 'red')
        # sys.exit() #delete
        return False
    
