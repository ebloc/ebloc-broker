#!/usr/bin/env python3

import subprocess, sys, os, pprint, json, shutil

from jsondiff import diff
from lib import compressFolder, log, StorageID, CacheType, printc
from contractCalls.submitJob       import submitJob
from contractCalls.getProviderInfo import getProviderInfo
from contract.scripts.lib          import cost
from imports import connect, connectEblocBroker, getWeb3

globals()['folderName_tarHash'] = {}

def gdriveUpload(folderToShare, jobKeyFlag=False):
    alreadyUploaded = False
    '''
    if folderType == 'folder': 
        tarHash = subprocess.check_output(['../scripts/generateMD5sum.sh', folderToShare]).decode('utf-8').strip()
        tarHash = tarHash.split(' ', 1)[0]
        print('hash=' + tarHash)

        if not os.path.isdir(tarHash):
            subprocess.run(['cp', '-a', folderToShare, tarHash])
        
        folderToShare = tarHash
        #cmd: gdrive list --query "name contains 'exampleFolderToShare'" --no-header
        res = subprocess.check_output(['gdrive', 'list', '--query', 'name contains \'' + folderToShare + '\'', '--no-header']).decode('utf-8').strip()
        if res is '':
            print('Uploading ...')
            #cmd: gdrive upload --recursive $folderToShare
            res = subprocess.check_output(['gdrive', 'upload', '--recursive', folderToShare]).decode('utf-8').strip()
            print(res)    
            res = subprocess.check_output(['gdrive', 'list', '--query', 'name contains \'' + folderToShare + '\'', '--no-header']).decode('utf-8').strip()
            key = res.split(' ')[0]
    '''
    if jobKeyFlag: # tar.gz inside a folder
        # TODO: icine dataFiles 'i gom
        dir_path = os.path.dirname(folderToShare)          
        ipfsHash, tarHash = compressFolder(folderToShare)
        if not os.path.exists(dir_path + '/' + tarHash):
            os.mkdir(dir_path + '/' + tarHash)
            
        shutil.move(dir_path + '/' + tarHash + '.tar.gz', dir_path + '/' + tarHash + '/' + tarHash + '.tar.gz')
        shutil.copyfile(folderToShare + '/dataFiles.json', dir_path + '/' + tarHash + '/dataFiles.json')       
        
        res = subprocess.check_output(['gdrive', 'list', '--query', 'name=' + '\'' + tarHash + '\'', '--no-header']).decode('utf-8').strip()
        if res == '':        
            res = subprocess.check_output(['gdrive', 'upload', '--recursive', dir_path + '/' + tarHash]).decode('utf-8').strip()                        
            res = subprocess.check_output(['gdrive', 'list', '--query', 'name=' + '\'' + tarHash + '\'', '--no-header']).decode('utf-8').strip()
            key = res.split(' ')[0]
        else:
            printc('Requested folder ' + tarHash + ' is already uploaded', 'green')
            # print(res)
            key = res.partition('\n')[0].split()[0]
            alreadyUploaded = True

        shutil.rmtree(dir_path + '/' + tarHash) # created .tar.gz files are removed
    elif folderType == 'tar':
        dir_path = os.path.dirname(folderToShare)
        ipfsHash, tarHash = compressFolder(folderToShare)
        res = subprocess.check_output(['gdrive', 'list', '--query', 'name=' + '\'' + tarHash + '.tar.gz' + '\'', '--no-header']).decode('utf-8').strip()      
        # res = subprocess.check_output(['gdrive', 'list', '--query', 'name contains \'' + tarHash + '.tar.gz' + '\'', '--no-header']).decode('utf-8').strip()
        if res == '':
            # subprocess.run(['mv', folderToShare + '.tar.gz', tarHash + '.tar.gz'])                
            subprocess.run(['gdrive', 'upload', dir_path + '/' + tarHash + '.tar.gz'])    
            subprocess.run(['rm', '-f', dir_path + '/' + tarHash + '.tar.gz'])
            res = subprocess.check_output(['gdrive', 'list', '--query', 'name=' + '\'' + tarHash + '.tar.gz' + '\'', '--no-header']).decode('utf-8').strip()      
            # res = subprocess.check_output(['gdrive', 'list', '--query', 'name contains \'' + tarHash + '.tar.gz' + '\'', '--no-header']).decode('utf-8').strip()
            key = res.split(' ')[0]
        else:
            printc('Requested file ' + tarHash + '.tar.gz' + ' is already uploaded', 'green')
            key = res.partition('\n')[0].split()[0]
            subprocess.run(['rm', '-f', dir_path + '/' + tarHash + '.tar.gz']) # created .tar.gz files are removed
            alreadyUploaded = True
    '''
    elif folderType == 'zip':
        # zip -r myfiles.zip mydir
        subprocess.run(['zip', '-r', folderToShare + '.zip', folderToShare])
        tarHash = subprocess.check_output(['md5sum', folderToShare + '.zip']).decode('utf-8').strip()
        tarHash = tarHash.split(' ', 1)[0]

        shutil.move(folderToShare + '.zip', tarHash + '.zip')
        
        subprocess.run(['mv', folderToShare + '.zip', tarHash + '.zip'])
        
        subprocess.run(['gdrive', 'upload', tarHash + '.zip'])    
        subprocess.run(['rm', '-f', tarHash + '.zip'])
        print('hash=' + tarHash)
        res = subprocess.check_output(['gdrive', 'list', '--query', 'name contains \'' + tarHash + '.zip' + '\'', '--no-header']).decode('utf-8').strip()
        key = res.split(' ')[0]
    '''
    
    globals()['folderName_tarHash'][folderToShare] = {'ipfsHash': ipfsHash, 'tarHash': tarHash}
    # globals()['folderName_hash'][folderToShare] = tarHash    
    return key, alreadyUploaded

def shareFolder(folderToShare, providerToShare, jobKeyFlag=False):
    print('folderToShare=' + folderToShare)
    jobKey, alreadyUploaded = gdriveUpload(folderToShare, jobKeyFlag)
    _tarHash = folderName_tarHash[folderToShare]['tarHash']
    globals()['jobKey_dict'][_tarHash] = jobKey
    print('jobKey=' + jobKey)
    #cmd: gdrive share $jobKey --role writer --type user --email $providerToShare
    if not alreadyUploaded:
        res = subprocess.check_output(['gdrive', 'share', jobKey, '--role', 'writer', '--type', 'user', '--email', providerToShare]).decode('utf-8').strip()
        print('share_output=' + res)        
    
def gdriveSubmitJob(provider, eBlocBroker, w3):
    eBlocBroker, w3 = connect(eBlocBroker, w3)
    if eBlocBroker is None or w3 is None:
        return False, 'web3 is not connected'

    provider =  w3.toChecksumAddress(provider) # netlab
    providerToShare = 'alper.alimoglu@gmail.com' # 'alper01234alper@gmail.com'
    status, providerInfo = getProviderInfo(provider, eBlocBroker, w3)
    folderToShare_list  = [] # Path of folder to share

    cacheHour_list      = []
    coreMin_list        = []

    # Full path of the sourceCodeFolders is given
    globals()['folderType'] = 'tar' # fixed
    globals()['jobKey_dict'] = {}
    globals()['sourceCodeHash_list'] = []
    
    sourceCodePath='/home/netlab/eBlocBroker/gdrive/exampleFolderToShare/sourceCode'
    folderToShare_list.append(sourceCodePath) # sourceCode at index 0
    folderToShare_list.append('/home/netlab/eBlocBroker/gdrive/exampleFolderToShare/data1')
    # subprocess.run(['sudo', 'chmod', '-R', '777', folderToShare])
    
    try:
        if len(folderToShare_list) > 1:
            for i in range(1, len(folderToShare_list)):        
                folderToShare = folderToShare_list[i]
                shareFolder(folderToShare, providerToShare) # Attempting to share the data folder

            dataFileJson_path = folderToShare_list[0] + '/dataFiles.json'
            if os.path.isfile(dataFileJson_path):            
                with open(dataFileJson_path) as json_file:
                    data_j = json.load(json_file)

            if os.path.isfile(dataFileJson_path) and jobKey_dict == data_j:
                printc('dataFile.json file already exists', 'green')
            else:                
                with open(sourceCodePath + '/dataFiles.json', 'w') as f:
                    json.dump(jobKey_dict, f)
                printc('dataFile.json file is updated on the sourceCode folder', 'blue')

        folderToShare = folderToShare_list[0] # sourceCode
        shareFolder(folderToShare, providerToShare, True)
    except Exception as e:
        print('E: ' + e)
        sys.exit()                         

    print('\nSubmitting Job...')
    coreMin_list.append(5)
    coreNum         = 1
    core_list       = [1]
    dataTransferIn  = [1, 1]
    dataTransferOut = 1
    dataTransfer    = [dataTransferIn, dataTransferOut]
    storageID       = [StorageID.GDRIVE.value, StorageID.GDRIVE.value]
    # cacheType     = CacheType.PRIVATE.value # Works
    # cacheType     = CacheType.PUBLIC.value
    cacheType       = CacheType.IPFS.value
    cacheHour_list  = [1, 1]

    for i in range(0, len(folderToShare_list)):
        _tarHash = folderName_tarHash[folderToShare_list[i]]['tarHash']
        sourceCodeHash = w3.toBytes(text=_tarHash) # required to send string as bytes == str_data.encode('utf-8')
        sourceCodeHash_list.append(sourceCodeHash)

    _tarHash  = folderName_tarHash[folderToShare_list[0]]['tarHash']
    jobKey = jobKey_dict[_tarHash]
    print('jobKey=' + jobKey)
    jobPriceValue, _cost = cost(core_list, coreMin_list, provider, sourceCodeHash_list, dataTransferIn, dataTransferOut, cacheHour_list, storageID, eBlocBroker, w3, False)

    accountID = 0
    status, result = submitJob(provider, jobKey, core_list, coreMin_list, dataTransferIn, dataTransferOut, storageID, sourceCodeHash_list, cacheType, cacheHour_list, accountID, jobPriceValue, eBlocBroker, w3)
    return status, result

if __name__ == "__main__":
    w3          = getWeb3()
    eBlocBroker = connectEblocBroker(w3)

    provider =  "0x57b60037b82154ec7149142c606ba024fbb0f991" # netlab
    status, result = gdriveSubmitJob(provider, eBlocBroker, w3)
    
    if not status:
        print(result)
        sys.exit()
    else:
        print('tx_hash: ' + result)
        receipt = w3.eth.waitForTransactionReceipt(result)
        print("Transaction receipt mined: \n")
        pprint.pprint(dict(receipt))
        print("Was transaction successful?")
        pprint.pprint(receipt['status'])
        if receipt['status'] == 1:
            logs = eBlocBroker.events.LogJob().processReceipt(receipt)
            try:
                print("Job's index=" + str(logs[0].args['index']))
            except IndexError:
                print('Transaction is reverted.')
