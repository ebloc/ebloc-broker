#!/usr/bin/env python3

import hashlib, getpass, sys, os, time, subprocess, lib, re, pwd, glob, errno, json, glob, traceback

from lib import convertByteToMB, sbatchCall, log, silentremove, PROGRAM_PATH, PROVIDER_ID
from colored import stylize, fg

from contractCalls.refund          import refund
from contractCalls.getJobInfo      import getJobInfo
from contractCalls.getProviderInfo import getProviderInfo

globals()['cacheType']         = None
globals()['index']             = None
globals()['globalCacheFolder'] = None
globals()['folderType_dict'] = {}
globals()['shareID']         = {}


def isRunExistInTar(tarPath):
    try:
        FNULL = open(os.devnull, 'w')
        res = subprocess.check_output(['tar', 'ztf', tarPath, '--wildcards', '*/run.sh'], stderr=FNULL).decode('utf-8').strip()
        FNULL.close()
        if res.count('/') == 1: # Main folder should contain the 'run.sh' file
            log('./run.sh exists under the parent folder', 'green')
            return True
        else:
            log('E: run.sh does not exist under the parent folder', 'red')
            return False        
    except:
        log('E: run.sh does not exist under the parent folder', 'red')
        return False
    
def cache_wrapper(resultsFolderPrev):    
    for i in range(0, len(sourceCodeHashText_list)):
        folderName = sourceCodeHashText_list[i]            
        status = cache(resultsFolderPrev, folderName, i)
        if not status:
            return False
    return True
        
def cache(resultsFolderPrev, folderName, _id):
    if cacheType == lib.CacheType.PRIVATE.value: # First checking does is already exist under public cache directory
        globals()['globalCacheFolder'] = publicDir
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
                    log('Already cached under the public directory...', 'green')                    
                    return True
        else:
            globals()['folderType_dict'][folderName] = 'tar.gz'           
            res = subprocess.check_output(['bash', lib.EBLOCPATH + '/scripts/generateMD5sum.sh', cachedTarFile]).decode('utf-8').strip()
            if res == folderName: # Checking is already downloaded folder's hash matches with the given hash
                globals()['cacheType'] = lib.CacheType.PUBLIC.value
                log('Already cached under the public directory.', 'green')                
                return True
    
    if cacheType == lib.CacheType.PRIVATE.value or cacheType == lib.CacheType.PUBLIC.value: 
        if cacheType == lib.CacheType.PRIVATE.value:
            # Download into private directory at $HOME/.eBlocBroker/cache
            globals()['globalCacheFolder'] = privateDir
        elif cacheType == lib.CacheType.PUBLIC.value:
            globals()['globalCacheFolder'] = publicDir
        
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
                    log(folderName + ' is already cached under the public directory.', 'green')
                    return True
                else:
                    if not eudatDownloadFolder(globalCacheFolder, cachedFolder, folderName):
                        return False
            else:        
                if not eudatDownloadFolder(globalCacheFolder, cachedFolder, folderName):
                    return False
            
            if _id == 0 and folderType_dict[folderName] == 'tar.gz' and not isRunExistInTar(cachedTarFile):
                silentremove(cachedTarFile)
                return False
        else: # Here we already know that its tar.gz file
            globals()['folderType_dict'][folderName] = 'tar.gz'           
            res = subprocess.check_output(['bash', lib.EBLOCPATH + '/scripts/generateMD5sum.sh', cachedTarFile]).decode('utf-8').strip()
            # if folderType_dict[folderName] == 'tar.gz':
            #    res = subprocess.check_output(['bash', lib.EBLOCPATH + '/scripts/generateMD5sum.sh', cachedTarFile]).decode('utf-8').strip()
            # elif folderType_dict[folderName] == 'folder':
            #    res = subprocess.check_output(['bash', lib.EBLOCPATH + '/scripts/generateMD5sum.sh', cachedFolder]).decode('utf-8').strip()
            if res == folderName: #Checking is already downloaded folder's hash matches with the given hash
                log(folderName + '.tar.gz is already cached.', 'green')
                return True
            else:
                 if not eudatDownloadFolder(globalCacheFolder, cachedFolder, folderName):
                    return False
    return True

# Assumes job is sent as .tar.gz file
def eudatDownloadFolder(resultsFolderPrev, resultsFolder, folderName) -> bool:    
    log('Downloading output.zip for ' + folderName + ' -> ' + resultsFolderPrev + '/' + folderName + '.tar.gz' + '  ... ', 'blue', False)
    for attempt in range(5):
        try:
            f_name = '/' + folderName + '/' + folderName + '.tar.gz'
            status = oc.get_file(f_name, resultsFolderPrev + '/' + folderName + '.tar.gz')
            if status:
                log('Done', 'blue')
            else:
                return False
        except Exception:
            log('')
            log('E: Failed to download eudat file.', 'red')
            log(traceback.format_exc(), 'red')
            time.sleep(5)
        else:
            break
    else:
        status, result = refund(PROVIDER_ID, PROVIDER_ID, jobKey, index, jobID, sourceCodeHash_list) # Complete refund backte requester
        if not status:
            log(result, 'red')
        else:
            log('refund()_tx_hash=' + result)
        return False # Should return back to Driver

    return True
    
def eudatGetShareToken():
    """Checks already shared or not."""
    folderTokenFlag = {}        
    if not os.path.isdir(privateDir):
        log(privateDir + ' does not exist', 'red')
        return
    
    shareID_file = privateDir + '/' + jobKey + '_shareID.json'
    acceptFlag = 0
    for i in range(0, len(sourceCodeHashText_list)):
        folderName = sourceCodeHashText_list[i]              
        
        globals()['folderType_dict'][folderName] = None # initialization
        if os.path.isdir(lib.OWN_CLOUD_PATH + '/' + folderName):
            log('Eudat shared folder(' + folderName + ') is already accepted and exists on the Eudat mounted folder...', 'green')              
            if os.path.isfile(lib.OWN_CLOUD_PATH + '/' + folderName + '/' + folderName + '.tar.gz'):
                globals()['folderType_dict'][folderName] = 'tar.gz'                
            else:
                globals()['folderType_dict'][folderName] = 'folder'
        try:
            info = oc.file_info('/' + folderName + '/' + folderName + '.tar.gz')
            size = info.attributes['{DAV:}getcontentlength']
            folderTokenFlag[folderName] = True                        
            log('size of ' + '/' + folderName + '/' + folderName + '.tar.gz => ' + str(size) + ' bytes')
            acceptFlag += 1
        except Exception:
            folderTokenFlag[folderName] = False

    if os.path.isfile(shareID_file) and os.path.getsize(shareID_file) > 0:
        with open(shareID_file) as json_file:
            globals()['shareID'] = json.load(json_file)
    
    log("shareID_dict=" + str(shareID))
    for attempt in range(5):
        try:
            shareList = oc.list_open_remote_share()
        except Exception:
            log('E: Failed to list_open_remote_share eudat.', 'red')
            log(traceback.format_exc(), 'red')
            time.sleep(1)
        else:
            break
    else:
        return False       

    acceptFlag = 0
    for i in range(0, len(sourceCodeHashText_list)):
        folderName = sourceCodeHashText_list[i]
        if folderTokenFlag[folderName]:
            acceptFlag += 1            
        else:
            eudatFolderName = ""
            log("Searching shareTokens for the related source code folder...")
            for i in range(len(shareList)-1, -1, -1): # Starts iterating from last item to the first one
                inputFolderName  = shareList[i]['name']
                inputFolderName  = inputFolderName[1:] # Removes '/' on the beginning of the string
                _shareID         = shareList[i]['id']
                inputOwner       = shareList[i]['owner']
                inputUser        = shareList[i]['user'] + '@b2drop.eudat.eu'
                if inputFolderName == folderName and inputUser == fID:                
                    shareToken = str(shareList[i]['share_token'])
                    globals()['shareID'][folderName] = {'shareID': int(_shareID), 'shareToken': shareToken}                        
                    eudatFolderName  = str(inputFolderName)                    
                    log("Found. Name=" + folderName + " |ShareID=" + _shareID + " |ShareToken=" + shareToken)
                    oc.accept_remote_share(int(_shareID))
                    log('shareID is accepted.', 'green')
                    acceptFlag += 1
                    break        
        if acceptFlag is len(sourceCodeHash_list):
            break
    else:
        log("E: Couldn't find a shared file. Found ones are: " + str(shareID), 'red')
        return False

    with open(shareID_file, 'w') as f:
        json.dump(shareID, f)

    size_to_download = 0
    for i in range(0, len(sourceCodeHashText_list)):
        folderName = sourceCodeHashText_list[i]
        if not shouldAlreadyCached[folderName]:
            info = oc.file_info('/' + folderName + '/' + folderName + '.tar.gz')
            size_to_download += int(info.attributes['{DAV:}getcontentlength'])
            
    log('Total size to download=' + str(size_to_download))
    return True, int(convertByteToMB(size_to_download))
                               
def driverEudat(loggedJob, jobInfo, requesterID, shouldAlreadyCached, eBlocBroker, w3, oc) -> bool:
    status, providerInfo = getProviderInfo(loggedJob.args['provider'])
    globals()['fID']       = providerInfo['fID']    
    globals()['jobKey']    = loggedJob.args['jobKey']
    globals()['index']     = loggedJob.args['index']
    globals()['storageID'] = loggedJob.args['storageID']
    globals()['cacheType'] = loggedJob.args['cacheType']
    
    globals()['dataTransferIn']      = jobInfo[0]['dataTransferIn']
    globals()['sourceCodeHash_list'] = loggedJob.args['sourceCodeHash']
    globals()['shouldAlreadyCached'] = shouldAlreadyCached
    globals()['sourceCodeHashText_list'] = []
    globals()['oc'] = oc

    globals()['publicDir']  = PROGRAM_PATH +'/cache'
    globals()['privateDir'] = PROGRAM_PATH + '/' + requesterID + '/cache'
    jobID = 0

    # ----------
    # TODO: delete 
    status, result = refund(PROVIDER_ID, PROVIDER_ID, jobKey, index, jobID, sourceCodeHash_list)
    if not status:
        log(tx_hash, 'red')
        return False
    else:
        log('refund()_tx_hash=' + result)
        return True
    sys.exit()
    # ----------
    
    resultsFolderPrev = PROGRAM_PATH + "/" + requesterID + "/" + jobKey + "_" + str(index)
    resultsFolder     = resultsFolderPrev + '/JOB_TO_RUN' 

    for i in range(0, len(sourceCodeHash_list)):
        sourceCodeHashText_list.append(w3.toText(sourceCodeHash_list[i]))

    status, used_dataTransferIn = eudatGetShareToken()
    if not status:
        return False

    if used_dataTransferIn > dataTransferIn:
        log('E: requested size to download the sourceCode and datafiles is greater that the given amount.')
        status, result = refund(PROVIDER_ID, PROVIDER_ID, jobKey, index, jobID, sourceCodeHash_list) # Full refund
        if not status:
            log(tx_hash, 'red')
            return False
        else:
            log('refund()_tx_hash=' + result)
            return True
    
    status = cache_wrapper(resultsFolderPrev)        
    if not status:
        return False
    
    if not os.path.isdir(resultsFolderPrev): # If folder does not exist
        os.makedirs(resultsFolderPrev)
        os.makedirs(resultsFolder)

    if not os.path.isdir(resultsFolder):
        os.makedirs(resultsFolder)
                
    for i in range(0, len(sourceCodeHashText_list)):        
        folderName = sourceCodeHashText_list[i]
        if folderType_dict[folderName] == 'tar.gz':
            # Untar cached tar file into private directory
            subprocess.run(['tar', '-xf', globalCacheFolder + '/' + folderName + '.tar.gz', '--strip-components=1', '-C', resultsFolder])
    try:        
        log('dataTransferIn=' + str(dataTransferIn))
        shareToken = shareID[jobKey]['shareToken']
        sbatchCall(loggedJob, shareToken, requesterID, resultsFolder, resultsFolderPrev, dataTransferIn, sourceCodeHash_list, jobInfo, eBlocBroker,  w3)
    except Exception:
        log('E: Failed to call sbatchCall() function.')
        log(traceback.format_exc(), 'red')
        return False
    
