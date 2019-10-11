#!/usr/bin/env python3

import hashlib, getpass, sys, os, time, subprocess, lib, re, pwd, glob, errno, json, glob
from colored import stylize, fg
from contractCalls.getJobInfo      import getJobInfo
from contractCalls.getProviderInfo import getProviderInfo

globals()['cacheType']         = None
globals()['index']             = None
globals()['globalCacheFolder'] = None
globals()['dataTransferIn']  = 0 # If the requested file is already cached, it stays as 0 
globals()['shareToken_dict'] = {}
globals()['folderType_dict'] = {}
globals()['ipfsHash_dict']   = {}

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
        lib.log('Error: run.sh does not exist under the parent folder', 'red')
        return False

def isTarExistsInZip(resultsFolderPrev, folderName):
    # cmd: unzip -l $resultsFolder/output.zip | grep $eudatFolderName/run.sh
    # Checks does zip contains .tar.gz file or not
    p1 = subprocess.Popen(['unzip', '-l', resultsFolderPrev + '/output.zip'], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(['grep', jobKey + '.tar.gz'], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    out = p2.communicate()[0].decode('utf-8').strip()    
    if jobKey + '.tar.gz' in out:
        globals()['folderType_dict'][folderName] = 'tar.gz'
    else:
        globals()['folderType_dict'][folderName] = 'folder'
        
    lib.log('folderType=' + folderType_dict[folderName])

def cache_wrapper(requesterID, resultsFolderPrev):    
    for i in range(0, len(sourceCodeHashText_list)):
        folderName = sourceCodeHashText_list[i]
        status = cache(requesterID, resultsFolderPrev, folderName)
        if not status:
            return False
    return True
        
def cache(requesterID, resultsFolderPrev, folderName):
    if cacheType ==lib.CacheType.PRIVATE.value: # First checking does is already exist under public cache directory
        globals()['globalCacheFolder'] = lib.PROGRAM_PATH +'/cache'
        if not os.path.isdir(globalCacheFolder): # If folder does not exist
            os.makedirs(globalCacheFolder)
                   
        cachedFolder  = globalCacheFolder + '/' + folderName
        cachedTarFile = globalCacheFolder + '/' + folderName + '.tar.gz'
        
        if not os.path.isfile(cachedTarFile):
            if os.path.isfile(cachedFolder + '/run.sh'):
                res = subprocess.check_output(['bash', lib.EBLOCPATH + '/scripts/generateMD5sum.sh', cachedFolder]).decode('utf-8').strip()
                if res == folderName: #Checking is already downloaded folder's hash matches with the given hash
                    globals()['folderType_dict'][folderName] = 'folder'                    
                    globals()['cacheType'] = lib.CacheType.PUBLIC.value
                    lib.log('Already cached under public directory...', 'green')                    
                    return True
        else:
            globals()['folderType_dict'][folderName] = 'tar.gz'           
            res = subprocess.check_output(['bash', lib.EBLOCPATH + '/scripts/generateMD5sum.sh', cachedTarFile]).decode('utf-8').strip()
            if res == folderName: # Checking is already downloaded folder's hash matches with the given hash
                globals()['cacheType'] = lib.CacheType.PUBLIC.value
                lib.log('Already cached under the public directory.', 'green')                
                return True
    
    if cacheType == lib.CacheType.PRIVATE.value or cacheType == lib.CacheType.PUBLIC.value: # Download into private directory at $HOME/.eBlocBroker/cache
        if cacheType == lib.CacheType.PRIVATE.value:
            globals()['globalCacheFolder'] = lib.PROGRAM_PATH + '/' + requesterID + '/cache'
        elif cacheType == lib.CacheType.PUBLIC.value:
            globals()['globalCacheFolder'] = lib.PROGRAM_PATH +'/cache'
        
        if not os.path.isdir(globalCacheFolder): # If folder does not exist
            os.makedirs(globalCacheFolder)
                   
        cachedFolder  = globalCacheFolder + '/' + folderName
        cachedTarFile = cachedFolder + '.tar.gz'
        if not os.path.isfile(cachedTarFile):
            # if os.path.isfile(cachedFolder + '/run.sh'):
            if os.path.isdir(cachedFolder):
                res = subprocess.check_output(['bash', lib.EBLOCPATH + '/scripts/generateMD5sum.sh',
                                               cachedFolder + '/' + folderName + '.tar.gz']).decode('utf-8').strip()
                if res == folderName: # Checking is already downloaded folder's hash matches with the given hash
                    globals()['folderType_dict'][folderName] = 'folder'                    
                    lib.log(folderName + ' is already cached under the public directory.', 'green')
                    return True
                else:
                    if not eudatDownloadFolder(globalCacheFolder, cachedFolder, folderName):
                        return False
            else:        
                if not eudatDownloadFolder(globalCacheFolder, cachedFolder, folderName):
                    return False
            
            if folderType_dict[folderName] == 'tar.gz' and not isRunExistInTar(cachedTarFile):
                lib.silentremove(cachedTarFile)
                return False
        else: # Here we already know that its tar.gz file
            globals()['folderType_dict'][folderName] = 'tar.gz'           
            res = subprocess.check_output(['bash', lib.EBLOCPATH + '/scripts/generateMD5sum.sh', cachedTarFile]).decode('utf-8').strip()
            # if folderType_dict[folderName] == 'tar.gz':
            #    res = subprocess.check_output(['bash', lib.EBLOCPATH + '/scripts/generateMD5sum.sh', cachedTarFile]).decode('utf-8').strip()
            # elif folderType_dict[folderName] == 'folder':
            #    res = subprocess.check_output(['bash', lib.EBLOCPATH + '/scripts/generateMD5sum.sh', cachedFolder]).decode('utf-8').strip()
            if res == folderName: #Checking is already downloaded folder's hash matches with the given hash
                lib.log(folderName + '.tar.gz is already cached.', 'green')
                return True
            else:
                if not eudatDownloadFolder(globalCacheFolder, cachedFolder, folderName):
                    return False                
    elif cacheType == lib.CacheType.IPFS.value:
        lib.log('Adding from owncloud mount point into IPFS...', 'blue')
        tarFile = lib.OWN_CLOUD_PATH + '/' + folderName + '/' + folderName + '.tar.gz'        
        if os.path.isfile(tarFile):            
            globals()['folderType_dict'][folderName] = 'tar.gz'
            ipfsHash = subprocess.check_output(['ipfs', 'add', tarFile]).decode('utf-8').strip() #TODO: add try catch, try few times if error generated
        else:
            globals()['folderType_dict'][folderName] = 'folder'
            ipfsHash = subprocess.check_output(['ipfs', 'add', '-r', lib.OWN_CLOUD_PATH + '/' + folderName]).decode('utf-8').strip()            
            ipfsHash = ipfsHash.splitlines()
            ipfsHash = ipfsHash[int(len(ipfsHash) - 1)] # Last line of ipfs hash output is obtained which has the root folder's hash
            globals()['ipfsHash_dict'][folderName] = ipfsHash.split()[1]
        return True

    return True

# Assume job is sent as .tar.gz file
def eudatDownloadFolder(resultsFolderPrev, resultsFolder, folderName):    
    lib.log('Downloading output.zip for' + folderName + ' -> ' + resultsFolderPrev + '/output.zip', 'blue')
    for attempt in range(5):
        try:
            # cmd: wget --continue -4 -o /dev/stdout https://b2drop.eudat.eu/s/$shareToken/download --output-document=$resultsFolderPrev/output.zip
            ret = subprocess.check_output(['wget', '--continue', '-4', '-o', '/dev/stdout', 'https://b2drop.eudat.eu/s/' + shareToken[folderName] +
                                           '/download', '--output-document=' + resultsFolderPrev + '/output.zip']).decode('utf-8')
            lib.log(ret) 
        except Exception as e:
            lib.log('Failed to download eudat file: '+ str(e), 'red')
            time.sleep(5)
        else:
            break;
    else:
        return False

    if "ERROR 404: Not Found" in ret:
        lib.log(ret, 'red') 
        lib.log('File not found The specified document has not been found on the server.', 'red') 
        # TODO: since folder does not exist, do complete refund to the user.
        return False
    
    result = re.search('Length: (.*) \(', ret) # https://stackoverflow.com/a/6986163/2402577 , re.search() == Regular expression operations
    if result is not None: # from wget output
        globals()['dataTransferIn'] = lib.convertByteToMB(result.group(1)) # Downloaded file size in MBs
    else: # from downloaded files size in bytes
        # p1 = subprocess.Popen(['du', '-b', resultsFolderPrev + '/output.zip'], stdout=subprocess.PIPE)
        p1 = subprocess.Popen(['ls', '-ln', resultsFolderPrev + '/output.zip'], stdout=subprocess.PIPE)
        # p2 = subprocess.Popen(['awk', '{print $1}'], stdin=p1.stdout, stdout=subprocess.PIPE)
        p2 = subprocess.Popen(['awk', '{print $5}'], stdin=p1.stdout, stdout=subprocess.PIPE)
        p1.stdout.close()
        out = p2.communicate()[0].decode('utf-8').strip() # Retunrs downloaded files size in bytes       
        globals()['dataTransferIn'] = lib.convertByteToMB(out)  # Downloaded file size in MBs

    lib.log('dataTransferIn=' + str(dataTransferIn) + ' MB', 'green')           
    isTarExistsInZip(resultsFolderPrev, folderName)   
    time.sleep(0.25) 
    if os.path.isfile(resultsFolderPrev + '/output.zip'):        
        if folderType_dict[folderName]  == 'tar.gz':
            command = ['unzip', '-jo', resultsFolderPrev + '/output.zip', '-d', resultsFolderPrev, '-x'] + glob.glob('*result-*.tar.gz')
            subprocess.run(command)
        else:
            command = ['unzip', '-jo', resultsFolderPrev + '/output.zip', '-d', resultsFolder] + glob.glob('*result-*.tar.gz')
            subprocess.run(command)

        lib.silentremove(resultsFolderPrev + '/output.zip')
        
    return True

# Checks already shared or not
def eudatGetShareToken(requesterID):
    shareToken_file = lib.PROGRAM_PATH + '/' + requesterID + '/cache' + '/' + jobKey + '_shareToken.json'
   # TODO: store shareToken id with folderName in some file, later do: oc.decline_remote_share(int(<share_id>)) to cancel shared folder at endCode or after some time later
    for i in range(0, len(sourceCodeHashText_list)):
        folderName = sourceCodeHashText_list[i]
        globals()['folderType_dict'][folderName] = None # initialization
        if cacheType == lib.CacheType.IPFS.value and os.path.isdir(lib.OWN_CLOUD_PATH + '/' + folderName):
            lib.log('Eudat shared folder is already accepted and exist on Eudat mounted folder...', 'green')              
            if os.path.isfile(lib.OWN_CLOUD_PATH + '/' + folderName + '/' + folderName + '.tar.gz'):
                globals()['folderType_dict'][folderName] = 'tar.gz'                
            else:
                globals()['folderType_dict'][folderName] = 'folder'
                
    if os.path.isfile(shareToken_file) and os.path.getsize(shareToken_file) > 0:
        with open(shareToken_file) as json_file:
            globals()['shareToken_dict'] = json.load(json_file)  
                   
        lib.log("ShareToken=" + str(shareToken_dict))
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
    lib.log("Searching shareTokens for the related source code folder")
    for i in range(len(shareList)-1, -1, -1): # Starts iterating from last item to the first one
        inputFolderName  = shareList[i]['name']
        inputFolderName  = inputFolderName[1:] # Removes '/' on the beginning
        inputID          = shareList[i]['id']
        inputOwner       = shareList[i]['owner']
        inputUser        = shareList[i]['user'] + '@b2drop.eudat.eu'
        # print(shareList[i])
        for j in range(0, len(sourceCodeHashText_list)):          
            folderName = sourceCodeHashText_list[j]
            if inputFolderName == folderName and inputUser == fID:                
                shareToken = str(shareList[i]['share_token'])
                globals()['shareToken_dict'][folderName] = shareToken
                
                eudatFolderName  = str(inputFolderName)
                acceptFlag += 1
                lib.log("Found. Name=" + folderName + " |InputId=" + inputID + " |ShareToken=" + shareToken)
                saveDirShareToken = lib.PROGRAM_PATH + '/' + requesterID + '/cache'
                if not os.path.isdir(saveDirShareToken):
                    lib.log(saveDirShareToken + ' does not exist', 'red')
                    return
                
                if cacheType == lib.CacheType.IPFS.value:
                    val = oc.accept_remote_share(int(inputID));
                    tryCount = 0
                    while True:
                        sleepDuration = 5
                        lib.log('Sleeping ' + str(sleepDuration) + ' seconds for accepted folder to emerge on the mounted Eudat folder...')
                        time.sleep(sleepDuration)
                        if tryCount is 5:
                            lib.log("Mounted Eudat does not see shared folder's path.", 'red')
                            return False
                 
                        if os.path.isdir(lib.OWN_CLOUD_PATH + '/' + folderName): # Checking is shared file emerged on mounted owncloud directory
                            break
                      
                        tryCount += 1

            if acceptFlag is len(sourceCodeHash_list):
                break
     
    if acceptFlag != len(sourceCodeHash_list):
        lib.log("Error: Couldn't find a shared file. Found ones are: " + str(shareToken_dict), 'red')
        oc.logout()         
        return False

    with open(shareToken_file, 'w') as f:
        json.dump(shareToken_dict, f)
  
    return True
                               
def driverEudat(loggedJob, jobInfo, requesterID, eBlocBroker, w3, oc) -> bool:
    status, providerInfo = getProviderInfo(loggedJob.args['provider'])
    globals()['fID']       = providerInfo['fID']    
    globals()['jobKey']    = loggedJob.args['jobKey']
    globals()['index']     = loggedJob.args['index']
    globals()['storageID'] = loggedJob.args['storageID'] # == 1
    globals()['cacheType'] = loggedJob.args['cacheType']
    globals()['sourceCodeHash_list'] = loggedJob.args['sourceCodeHash']
    globals()['sourceCodeHashText_list'] = []
    globals()['oc'] = oc
       
    resultsFolderPrev = lib.PROGRAM_PATH + "/" + requesterID + "/" + jobKey + "_" + str(index)
    resultsFolder     = resultsFolderPrev + '/JOB_TO_RUN' 

    for i in range(0, len(sourceCodeHash_list)):
        sourceCodeHash = w3.toText(sourceCodeHash_list[i])
        sourceCodeHashText_list.append(sourceCodeHash)
    
    if not eudatGetShareToken(requesterID):
        return False
    
    if cacheType != lib.CacheType.NONE.value:
        status= cache_wrapper(requesterID, resultsFolderPrev)
        
    if not status:
        return   
    
    if not os.path.isdir(resultsFolderPrev): # If folder does not exist
        os.makedirs(resultsFolderPrev)
        os.makedirs(resultsFolder)
                
    for i in range(0, len(sourceCodeHashText_list)):        
        folderName = sourceCodeHashText_list[i]
        if cacheType == lib.CacheType.PRIVATE.value or cacheType == lib.CacheType.PUBLIC.value:
            '''
            if cacheType == lib.CacheType.PRIVATE.value:
                globals()['globalCacheFolder'] = lib.PROGRAM_PATH + '/' + requesterID + '/cache'
            elif cacheType == lib.CacheType.PUBLIC.value:
                globals()['globalCacheFolder'] = lib.PROGRAM_PATH +'/cache'
            '''
            # Untar cached tar file into private directory
            if folderType_dict[folderName] == 'tar.gz':
                subprocess.run(['tar', '-xf', globalCacheFolder + '/' + folderName + '.tar.gz', '--strip-components=1', '-C', resultsFolder])
            elif folderType_dict[folderName] == 'folder':
                subprocess.run(['rsync', '-avq', '--partial-dir', '--omit-dir-times', globalCacheFolder + '/' + folderName + '/', resultsFolder])
                subprocess.run(['tar', '-xf', resultsFolder + '/' + folderName + '.tar.gz', '--strip-components=1', '-C', resultsFolder])                
        elif cacheType == lib.CacheType.IPFS.value:
            ipfsHash = globals()['ipfsHash_dict'][folderName]
            lib.log('Reading from IPFS hash=' + ipfsHash)
            if folderType_dict[folderName] == 'tar.gz':
                subprocess.run(['tar', '-xf', '/ipfs/' + ipfsHash, '--strip-components=1', '-C', resultsFolder])
            elif eudatFolderType == 'folder':
                # Copy from cached IPFS folder into user's path
                command = ['ipfs', 'get', ipfsHash, '-o', resultsFolder] # cmd: ipfs get <ipfs_hash> -o <resultsFolder>
                subprocess.run(command)

    try:        
        lib.log('dataTransferIn=' + str(dataTransferIn))
        shareToken_result = shareToken_dict[jobKey]
        lib.sbatchCall(loggedJob, shareToken_result, requesterID, resultsFolder, resultsFolderPrev, dataTransferIn, sourceCodeHash_list, jobInfo, eBlocBroker,  w3)
    except Exception as e:
        lib.log('Failed to call sbatchCall() function: ' + str(e), 'red')
        return False
