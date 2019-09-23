#!/usr/bin/env python3

import os, sys, time, enum, pprint
import lib

from imports import connect, connectEblocBroker, getWeb3
from contract.scripts.lib import cost
from contract.scripts.lib import convertIpfsToBytes32
from contractCalls.getProviderInfo import getProviderInfo

def submitJob(provider, jobKey, core, coreMin, dataTransferIn_list, dataTransferOut, storageID, sourceCodeHash_list, cacheType, cacheHour, accountID, jobPriceValue, eBlocBroker=None, w3=None):
    eBlocBroker, w3 = connect(eBlocBroker, w3)        
    if eBlocBroker is None or w3 is None:        
        return False, 'E: web3 is not connected'

    provider = w3.toChecksumAddress(provider)
    _from    = w3.toChecksumAddress(w3.eth.accounts[accountID] )

    status, providerInfo = getProviderInfo(provider, eBlocBroker, w3)
 
    providerPriceBlockNumber = eBlocBroker.functions.getProviderSetBlockNumbers(provider).call()[-1]
    storageID_cacheType = [storageID, cacheType, providerPriceBlockNumber]

    print("Provider's availableCoreNum: " + str(providerInfo['availableCoreNum']))
    print("Provider's priceCoreMin: "     + str(providerInfo['priceCoreMin'])) 

    my_filter = eBlocBroker.events.LogProviderInfo.createFilter(fromBlock=providerInfo['blockReadFrom'], toBlock=providerInfo['blockReadFrom'] + 1)

    if not eBlocBroker.functions.isProviderExists(provider).call(): 
        return False, "E: Requested provider's Ethereum Address \"" + provider + "\" does not registered."

    blockReadFrom, orcid = eBlocBroker.functions.getRequesterInfo(_from).call() 

    if not eBlocBroker.functions.isRequesterExists(_from).call():
        return False, "E: Requester's Ethereum Address \"" + _from + "\" does not exist."

    if eBlocBroker.functions.isRequesterOrcIDVerified(_from).call() == False:
        return False, 'E: Requester\'s orcid: ' + orcid + ' is not verified.'
    
    '''
    if lib.storageID.IPFS == storageID or lib.storageID.IPFS_MINILOCK == storageID:
       lib.isIpfsOn()
       strVal = my_filter.get_all_entries()[0].args['ipfsAddress']
       print('Trying to connect into ' + strVal)
       output = os.popen('ipfs swarm connect ' + strVal).read() 
       if 'success' in output:
          print(output)
    '''

    '''
    print(sourceCodeHash_list[0].encode('utf-8'))
    for i in range(len(sourceCodeHash_list)):
        sourceCodeHash_list[i] = sourceCodeHash_list[i]
        if len(sourceCodeHash_list[i]) != 32 and len(sourceCodeHash_list[i]) != 0:
            return False, 'sourceCodeHash_list should be 32 characters.'
    '''
    if not sourceCodeHash_list:
        return False, 'E: sourceCodeHash list is empty.'

    if len(jobKey) != 46 and (lib.StorageID.IPFS.value == storageID or lib.StorageID.IPFS_MINILOCK.value == storageID):
        return False,  "E: jobKey's length does not match with its original length, it should be 46. Please check your jobKey length"

    if len(jobKey) != 33 and lib.StorageID.GDRIVE.value == storageID:
        return False,  "E: jobKey's length does not match with its original length, it should be 33. Please check your jobKey length"

    for i in range(len(core)):        
        if core[i] > providerInfo['availableCoreNum']:
            return False, "E: Requested core[" + str(i) + "], which is " + str(core[i]) + ", is greater than the provider's core number"        
        if coreMin[i] == 0: 
            return False, 'E: coreMin[' + str(i) +'] is provided as 0. Please provide non-zero value'

    if int(storageID) > 4:
        return False, 'E: Wrong storageID value is given. Please provide from 0 to 4'
    
    if len(jobKey) >= 64:
        return False, 'E: Length of jobKey is greater than 64, please provide lesser'

    for i in range(len(coreMin)):        
        if coreMin[i] > 1440: 
            return False, 'E: coreMin provided greater than 1440. Please provide smaller value'
    
    if cacheType > 3: # {0:'private', 1:'public', 2:'none', 3:'ipfs'}
        return False, 'E: cachType provided greater than 1. Please provide smaller value'
    
    #if len(jobDescription) >= 128:
    #    return 'Length of jobDescription is greater than 128, please provide lesser.'
        
    try:
        gasLimit = 4500000
        print(sourceCodeHash_list)
        tx  = eBlocBroker.functions.submitJob(provider, jobKey, core, coreMin, dataTransferIn_list, dataTransferOut, storageID_cacheType, cacheHour, sourceCodeHash_list).transact({"from": _from, "value": jobPriceValue, "gas": gasLimit})
    except Exception:
        return False, traceback.format_exc()

    return True, str(tx.hex())

if __name__ == '__main__':
    w3          = getWeb3()
    eBlocBroker = connectEblocBroker(w3)

    if len(sys.argv) == 10:
        provider        = str(sys.argv[1])
        provider        = w3.toChecksumAddress(provider)                 
        jobKey          = str(sys.argv[2]) 
        core            = int(sys.argv[3]) 
        coreMin         = int(sys.argv[4])
        dataTransfer    = int(sys.argv[5])        
        storageID       = int(sys.argv[6])
        sourceCodeHash  = str(sys.argv[7])
        cacheHour       = int(sys.argv[8])
        accountID       = int(sys.argv[9]) # _from        
    elif len(sys.argv) == 13:
        provider        = str(sys.argv[1])
        provider        = w3.toChecksumAddress(provider)                 
        jobKey           = str(sys.argv[2]) 
        core             = int(sys.argv[3]) 
        coreGasDay       = int(sys.argv[4]) 
        coreGasHour      = int(sys.argv[5]) 
        coreGasMin       = int(sys.argv[6])
        dataTransferIn   = int(sys.argv[7])
        dataTransferOut  = int(sys.argv[8])
        storageID        = int(sys.argv[9])
        sourceCodeHash   = str(sys.argv[10]) 
        cacheHour      = int(sys.argv[11])
        accountID        = int(sys.argv[12])
        coreMin          = coreGasMin + coreGasHour * 60 + coreGasDay * 1440
        dataTransfer     = dataTransferIn + dataTransferOut
    else:   
        # ================================================ REQUESTER Inputs for testing ================================================
        storageID = lib.StorageID.IPFS.value
        _provider =  w3.toChecksumAddress('0x57b60037b82154ec7149142c606ba024fbb0f991') # netlab                        
        cacheType = lib.CacheType.PRIVATE.value # default
        cacheHour_list      = []
        sourceCodeHash_list = []
        coreMin_list        = []
        
        if storageID == lib.StorageID.IPFS.value: # IPFS
            jobKey      = 'QmbL46fEH7iaccEayKpS9FZnkPV5uss4SFmhDDvbmkABUJ'  # 30 seconds job                
            coreGasDay  = 0 
            coreGasHour = 0 
            coreGasMin  = 1
            coreMin     = coreGasMin + coreGasHour * 60 + coreGasDay * 1440
            coreMin_list.append(coreMin)

            # DataSourceCodes:
            ipfsBytes32    = convertIpfsToBytes32(jobKey)                
            sourceCodeHash_list.append(w3.toBytes(hexstr= ipfsBytes32))
            cacheHour_list.append(1)
                
            ipfsBytes32    = convertIpfsToBytes32('QmSYzLDW5B36jwGSkU8nyfHJ9xh9HLjMsjj7Ciadft9y65') # data1/data.txt
            sourceCodeHash_list.append(w3.toBytes(hexstr= ipfsBytes32))
            cacheHour_list.append(1)                
            cacheType = lib.CacheType.PUBLIC.value # default
        elif storageID == lib.StorageID.EUDAT.value:
            oc = owncloud.Client('https://b2drop.eudat.eu/')
            with open(lib.EBLOCPATH + '/eudatPassword.txt', 'r') as content_file:
                password = content_file.read().strip()
            oc.login(lib.OC_USER_ID, password)
            sourceCodeHash     = '00000000000000000000000000000000'
        elif storageID == lib.StorageID.GITHUB.value:
            print('Submitting through GitHub')
            jobKey = "avatar-lavventura=simpleSlurmJob"
            coreGasDay      = 0 
            coreGasHour     = 0 
            coreGasMin      = 1
            sourceCodeHash  = "acfd2fd8a1e9ccf031db0a93a861f6eb"                        
        
        core_list       = [1]        
        dataTransferIn_list  = [1, 1]
        dataTransferOut = 1        
        dataTransfer   = [dataTransferIn_list, dataTransferOut]            
        accountID = 0

    jobPriceValue, cost = cost(core_list, coreMin_list, _provider, sourceCodeHash_list, dataTransferIn_list, dataTransferOut, cacheHour_list, eBlocBroker, w3, False)
    status, result = submitJob(_provider, jobKey, core_list, coreMin_list, dataTransferIn_list, dataTransferOut, storageID, sourceCodeHash_list, cacheType, cacheHour_list, accountID, jobPriceValue, eBlocBroker, w3)
    
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
