#!/usr/bin/env python3

import os, sys, time, enum
import lib
from imports import connectEblocBroker, getWeb3



from contract.scripts.lib import cost

cost()

web3        = getWeb3()
eBlocBroker = connectEblocBroker(web3)

def submitJob(providerAddress, jobKey, core, coreMin, dataTransferIn, dataTransferOut, storageID, sourceCodeHash, cacheType, storageHour, accountID):
    providerAddress = web3.toChecksumAddress(providerAddress)  #POA

    providerPriceInfo = eBlocBroker.functions.getProviderInfo(providerAddress).call()
    blockReadFrom      = providerPriceInfo[0]
    availableCoreNum   = providerPriceInfo[1]
    priceCoreMin       = providerPriceInfo[2]
    priceDataTransfer  = providerPriceInfo[3]
    priceStorage       = providerPriceInfo[4]
    priceCache         = providerPriceInfo[5]
    commitmentBlockNum = providerPriceInfo[6]

    print("Provider's availableCoreNum: " + str(availableCoreNum))
    print("Provider's priceCoreMin: "     + str(priceCoreMin))
    
    my_filter = eBlocBroker.eventFilter('LogProviderInfo',{'fromBlock': int(blockReadFrom),'toBlock': int(blockReadFrom) + 1})    

    if not eBlocBroker.functions.isProviderExists(providerAddress).call(): 
        return False, "Error: Requested provider's Ethereum Address \"" + providerAddress + "\" does not exist."
    
    fromAccount = web3.eth.accounts[accountID] 
    fromAccount = web3.toChecksumAddress(fromAccount) 

    blockReadFrom, orcid = eBlocBroker.functions.getRequesterInfo(fromAccount).call() 

    if not eBlocBroker.functions.isRequesterExists(fromAccount).call():
        return False, "Error: Requested requester's Ethereum Address \"" + fromAccount + "\" does not exist."

    if eBlocBroker.functions.isRequesterOrcIDVerified(fromAccount).call() == False:
        return False, 'Error: Requester\'s orcid: ' + orcid + ' is not verified.'
   
    '''
    if storageID == 0 or storageID == 2:
       lib.isIpfsOn()
       strVal = my_filter.get_all_entries()[0].args['ipfsAddress']
       print('Trying to connect into ' + strVal)
       output = os.popen('ipfs swarm connect ' + strVal).read() 
       if 'success' in output:
          print(output)
    '''
    
    computationalCost = priceCoreMin * core * coreMin
    jobReceivedBlocNumber, jobGasStorageHour = eBlocBroker.functions.getJobStorageTime(fromAccount, sourceCodeHash).call();
    
    if jobReceivedBlocNumber + jobGasStorageHour * 240 > web3.eth.blockNumber:
        dataTransferIn = 0; # storageCost and cacheCost will be equaled to 0
        
    storageCost = priceStorage * dataTransferIn * storageHour
    cacheCost   = priceCache * dataTransferIn

    dataTransferSum  = dataTransferIn + dataTransferOut
    dataTransferCost = priceDataTransfer * dataTransferSum
    
    jobPriceValue = computationalCost + dataTransferCost + storageCost + cacheCost
    print("jobPriceValue: " + str(jobPriceValue))

    if len(sourceCodeHash) != 32 and len(sourceCodeHash) != 0:
        return False, 'Error: sourceCodeHash should be 32 characters.'
    if (storageID == 0 and len(jobKey) != 46) or (storageID == 2 and len(jobKey) != 46) or (storageID == 4 and len(jobKey) != 33): 
       return False,  "Error: jobKey's length does not match with its original length. Please check your jobKey."
    if core > availableCoreNum:
        return False, 'Error: Requested core number is greater than the provider\'s core number.'
    if int(storageID) > 4:
        return False, 'Error: Wrong storageID value is given. Please provide from 0 to 4.'
    if len(jobKey) >= 64:
        return False, 'Error: Length of jobKey is greater than 64, please provide lesser.'
    if coreMin == 0: 
        return False, 'Error: coreMin provided as 0. Please provide non-zero value'
    if coreMin > 1440: 
        return False, 'Error: coreMin provided greater than 1440. Please provide smaller value.'
    if cacheType > 3: # 0: 'private', 1: 'public', 2: 'none', 3: 'ipfs'
        return False, 'Error: cachType provided greater than 1. Please provide smaller value.'
    #if len(jobDescription) >= 128:
    #    return 'Error: Length of jobDescription is greater than 128, please provide lesser.'
        
    # print(providerAddress + " " + jobKey + " " + str(core) + " " + " " + str(coreMin) + " " + str(storageID) + ' ' + 'Value: ' + str(jobPriceValue))
    gasLimit = 4500000
    print(sourceCodeHash)
    tx_hash  = eBlocBroker.transact({"from": fromAccount,
                               "value": jobPriceValue,
                               "gas": gasLimit}).submitJob(providerAddress, jobKey, core, coreMin, dataTransferIn,
                                                           dataTransferOut, storageID, sourceCodeHash, cacheType, storageHour) 
    return True, tx_hash.hex(), str(computationalCost), str(storageCost), str(cacheCost), str(dataTransferCost), str(jobPriceValue)

if __name__ == '__main__': 
    test = 0    
    if len(sys.argv) == 10:
        providerAddress = str(sys.argv[1])
        providerAddress = web3.toChecksumAddress(providerAddress)                 
        jobKey          = str(sys.argv[2]) 
        core            = int(sys.argv[3]) 
        coreMin         = int(sys.argv[4])
        dataTransfer    = int(sys.argv[5])        
        storageID       = int(sys.argv[6])
        sourceCodeHash  = str(sys.argv[7])
        storageHour     = int(sys.argv[8])
        accountID       = int(sys.argv[9])        
    elif len(sys.argv) == 13: 
        providerAddress  = str(sys.argv[1])
        jobKey          = str(sys.argv[2]) 
        core            = int(sys.argv[3]) 
        coreGasDay      = int(sys.argv[4]) 
        coreGasHour     = int(sys.argv[5]) 
        coreGasMin      = int(sys.argv[6])
        dataTransferIn  = int(sys.argv[7])
        dataTransferOut = int(sys.argv[8])
        storageID       = int(sys.argv[9])
        sourceCodeHash  = str(sys.argv[10]) 
        storageHour     = int(sys.argv[11])
        accountID       = int(sys.argv[12])
        coreMin         = coreGasMin + coreGasHour * 60 + coreGasDay * 1440
        dataTransfer    = dataTransferIn + dataTransferOut
    else:   
        # REQUESTER Inputs ================================================================
        # providerAddress = web3.toChecksumAddress('0x4e4a0750350796164D8DefC442a712B7557BF282') #ebloc
        providerAddress = web3.toChecksumAddress('0x57b60037b82154ec7149142c606ba024fbb0f991') #netlab                
        storageID      = lib.storageID.github
        cacheType      = lib.cacheType.private # default
        
        if storageID == lib.storageID.ipfs: # IPFS
            longJob = False
            # jobKey    = '1-R0MoQj7Xfzu3pPnTqpfLUzRMeCTg6zG'           
            if longJob:
                jobKey         = 'QmXFVGtxUBLfR2cYPNQtUjRxMv93yzUdej6kYwV1fqUD3U' 
                coreGasDay     = 0 
                coreGasHour    = 0 
                coreGasMin     = 100
                hex_str        = lib.convertIpfsToBytes32(jobKey)
                sourceCodeHash = web3.toBytes(hexstr= hex_str)
                # sourceCodeHash  = "acfd2fd8a1e9ccf031db0a93a861f6eb"                
            else:
                jobKey         = 'QmY6jUjufnyB2nZe38hRZvmyboxtzRcPkP388Yjfhuomoy'  # 3 minutes job
                coreGasDay     = 0 
                coreGasHour    = 0 
                coreGasMin     = 3
                hex_str        = lib.convertIpfsToBytes32(jobKey)
                sourceCodeHash = web3.toBytes(hexstr= hex_str)
                               
            cacheType = lib.cacheType.public # default
            # TODO: convert into ===>  sourceCodeHash     = ''
        elif storageID == lib.storageID.github:
            print('Submitting through GitHub')
            jobKey = "avatar-lavventura=simpleSlurmJob"
            coreGasDay      = 0 
            coreGasHour     = 0 
            coreGasMin      = 1
            sourceCodeHash  = "acfd2fd8a1e9ccf031db0a93a861f6eb"
            
            
        '''    
        elif storageID == lib.storageID.eudat: # IPFS: TODO: update 
            oc = owncloud.Client('https://b2drop.eudat.eu/')
            with open(lib.EBLOCPATH + '/eudatPassword.txt', 'r') as content_file:
                password = content_file.read().strip()
            oc.login(lib.OC_USER_ID, password)
            sourceCodeHash     = '00000000000000000000000000000000'
        '''             
        #coreGasDay      = 0 
        #coreGasHour     = 0 
        #coreGasMin      = 1
        core            = 1 
        accountID       = 0
        coreMin      = coreGasMin + coreGasHour * 60 + coreGasDay * 1440
        dataTransferIn  = 100 
        dataTransferOut = 100
        storageHour  = 1
        # =============================================================================
        
    status, result = submitJob(providerAddress, jobKey, core, coreMin, dataTransferIn, dataTransferOut, storageID, sourceCodeHash, cacheType, storageHour, accountID)
    
    if not status:
        sys.exit()
            
    tx_hash = result[0]
    print('computationalCost:' + ret[1])
    print('storageCost:'       + ret[2])
    print('cacheCost:'         + ret[3])
    print('dataTransferCost:'  + ret[4])
    print('jobPriceValue:'     + ret[5])
    
    if 'Error' in tx_hash:
        print('Error: ' + tx_hash)
        sys.exit()
    
    print('Tx_hash: ' + tx_hash)    
    print('Waiting job to be deployed...')
    while True: 
        receipt = web3.eth.getTransactionReceipt(tx_hash)
        if receipt is None:
            time.sleep(2)
            receipt = web3.eth.getTransactionReceipt(tx_hash)
        else:
            logs = eBlocBroker.events.LogJob().processReceipt(receipt)
            try:
                print('Job\'s index=' + str(logs[0].args['index']))
                break
            except IndexError:
                print('Transaction is reverted.')
                break
