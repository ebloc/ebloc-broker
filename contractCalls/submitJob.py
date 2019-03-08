#!/usr/bin/env python3

import os, sys, time, enum
sys.path.insert(1, os.path.join(sys.path[0], '..'))
import lib
from imports import connectEblocBroker
from imports import getWeb3

web3        = getWeb3()
eBlocBroker = connectEblocBroker(web3)

def submitJob(clusterAddress, jobKey, core, gasCoreMin, dataTransferIn, dataTransferOut,
              jobDescription, storageID, sourceCodeHash, cacheType, gasStorageHour, accountID):
    clusterAddress = web3.toChecksumAddress(clusterAddress)  #POA
    # clusterAddress = web3.toChecksumAddress("0x75a4c787c5c18c587b284a904165ff06a269b48c")  #POW
    blockReadFrom, availableCoreNum, priceCoreMin, priceDataTransfer, priceStorage, priceCache = eBlocBroker.functions.getClusterInfo(clusterAddress).call() 
    my_filter = eBlocBroker.eventFilter('LogCluster',{'fromBlock':int(blockReadFrom),'toBlock':int(blockReadFrom) + 1})    

    if not eBlocBroker.functions.isClusterExist(clusterAddress).call(): 
       return "Error: Requested cluster's Ethereum Address \"" + clusterAddress + "\" does not exist."
    
    fromAccount = web3.eth.accounts[accountID] 
    fromAccount = web3.toChecksumAddress(fromAccount) 

    blockReadFrom, orcid = eBlocBroker.functions.getUserInfo(fromAccount).call() 

    if not eBlocBroker.functions.isUserExist(fromAccount).call():
       return "Error: Requested user's Ethereum Address \"" + fromAccount + "\" does not exist."       

    if str(eBlocBroker.functions.isUserOrcIDVerified(fromAccount).call()) == '0':
       return 'Error: User\'s orcid: ' + orcid + ' is not verified.'

    if storageID == 0 or storageID == 2:
       lib.isIpfsOn()
       strVal = my_filter.get_all_entries()[0].args['ipfsAddress'] 
       output = os.popen('ipfs swarm connect ' + strVal).read() 
       print('Trying to connect into: ' + strVal) 
       if 'success' in output:
          print(output)

    computationalCost = priceCoreMin * core * gasCoreMin
    jobReceivedBlocNumber, jobGasStorageHour = eBlocBroker.functions.getJobStorageTime(fromAccount, sourceCodeHash).call();
    if jobReceivedBlocNumber + jobGasStorageHour * 240 > web3.eth.blockNumber:
        dataTransferIn = 0; # storageCost and cacheCost will be equaled to 0
        
    storageCost = priceStorage * dataTransferIn * gasStorageHour
    cacheCost   = priceCache * dataTransferIn

    dataTransferSum  = dataTransferIn + dataTransferOut
    dataTransferCost = priceDataTransfer * dataTransferSum
    
    jobPriceValue = computationalCost + dataTransferCost + storageCost + cacheCost
    print("jobPriceValue: " + str(jobPriceValue))
        
    if not len(sourceCodeHash):
        return 'sourceCodeHash should be 32 characters.'    
    if (storageID == 0 and len(jobKey) != 46) or (storageID == 2 and len(jobKey) != 46) or (storageID == 4 and len(jobKey) != 33): 
       return "Error: jobKey's length does not match with its original length. Please check your jobKey."
    if core > availableCoreNum:
        return 'Error: Requested core number is greater than the cluster\'s core number.'
    if len(jobDescription) >= 128:
        return 'Error: Length of jobDescription is greater than 128, please provide lesser.'
    if int(storageID) > 4:
        return 'Error: Wrong storageID value is given. Please provide from 0 to 4.'
    if len(jobKey) >= 64:
        return 'Error: Length of jobDescription is greater than 64, please provide lesser.'
    if gasCoreMin == 0: 
        return 'Error: gasCoreMin provided as 0. Please provide non-zero value'
    if gasCoreMin > 1440: 
        return 'Error: gasCoreMin provided greater than 1440. Please provide smaller value.'
    if cacheType > 2: # 0: 'private', 1: 'public', 2: 'none'
        return 'Error: cachType provided greater than 1. Please provide smaller value.'
        
    # print(clusterAddress + " " + jobKey + " " + str(core) + " " + jobDescription + " " + str(gasCoreMin) + " " + str(storageID) + ' ' + 'Value: ' + str(jobPriceValue))
    gasLimit      = 4500000
    tx_hash = eBlocBroker.transact({"from": fromAccount,
                               "value": jobPriceValue,
                               "gas": gasLimit}).submitJob(clusterAddress, jobKey, core, gasCoreMin, dataTransferIn,
                                                           dataTransferOut, storageID, sourceCodeHash, cacheType, gasStorageHour) 
    return tx_hash.hex()

if __name__ == '__main__': 
    test = 0    
    if len(sys.argv) == 11:
        clusterAddress = str(sys.argv[1])
        clusterAddress = web3.toChecksumAddress(clusterAddress)                 
        jobKey          = str(sys.argv[2]) 
        core            = int(sys.argv[3]) 
        gasCoreMin      = int(sys.argv[4])
        gasDataTransfer = int(sys.argv[5])        
        jobDescription  = str(sys.argv[6])         
        storageID       = int(sys.argv[7])
        sourceCodeHash  = str(sys.argv[8])
        gasStorageHour  = int(sys.argv[9])
        accountID       = int(sys.argv[10])        
    elif len(sys.argv) == 14: 
        clusterAddress  = str(sys.argv[1])
        jobKey          = str(sys.argv[2]) 
        core            = int(sys.argv[3]) 
        coreGasDay      = int(sys.argv[4]) 
        coreGasHour     = int(sys.argv[5]) 
        coreGasMin      = int(sys.argv[6])
        dataTransferIn  = int(sys.argv[7])
        dataTransferOut = int(sys.argv[8])
        jobDescription  = str(sys.argv[9]) 
        storageID       = int(sys.argv[10])
        sourceCodeHash  = str(sys.argv[11]) 
        gasStorageHour  = int(sys.argv[12])
        accountID       = int(sys.argv[13])
        gasCoreMin      = coreGasMin + coreGasHour * 60 + coreGasDay * 1440
        gasDataTransfer = dataTransferIn + dataTransferOut

    else:   
        # USER Inputs ================================================================
        clusterAddress = web3.toChecksumAddress('0x4e4a0750350796164D8DefC442a712B7557BF282')
        storageID      = lib.storageID.ipfs
        cacheType      = lib.cacheType.private # default
        
        if storageID == lib.storageID.ipfs: # IPFS
            # jobKey    = '1-R0MoQj7Xfzu3pPnTqpfLUzRMeCTg6zG'           
            # jobKey    = 'QmWfcC6tWFq72LPoewTsXpH2kcjySenYQdiRhUERsmCYdg'  # 2 minutes job
            jobKey    = 'QmS5seSFGiPywJYkEAALCYHq3YgF4Pruq9eVz6Qmt4ZWms' # 20 seconds
            cacheType = lib.cacheType.public # default
            # TODO: convert into ===>  sourceCodeHash     = ''
            sourceCodeHash     = '00000000000000000000000000000000' # No need to provide any sourceCodeHash since it will store in the ipfs repository: TODO: provide anyway
        '''    
        elif storageID == lib.storageID.eudat: # IPFS: TODO: update 
            oc = owncloud.Client('https://b2drop.eudat.eu/')
            with open(lib.EBLOCPATH + '/eudatPassword.txt', 'r') as content_file:
                password = content_file.read().strip()
            oc.login(lib.OC_USER_ID, password)
            sourceCodeHash     = '00000000000000000000000000000000'
        '''     
        #jobKey         = 'QmRsaBEGcqxQcJbBxCi1LN9iz5bDAGDWR6Hx7ZvWqgqmdR' # Long Sleep Job.                        
        #jobKey         = "3d8e2dc2-b855-1036-807f-9dbd8c6b1579=folderName" 
        core            = 1 
        coreGasDay      = 0 
        coreGasHour     = 0 
        coreGasMin      = 1 
        jobDescription  = 'Science'        
        accountID       = 0
        gasCoreMin      = coreGasMin + coreGasHour * 60 + coreGasDay * 1440
        dataTransferIn  = 100 
        dataTransferOut = 100
        gasStorageHour  = 1
        # =============================================================================

    tx_hash = submitJob(clusterAddress, jobKey, core, gasCoreMin, dataTransferIn, dataTransferOut,
                        jobDescription, storageID, sourceCodeHash, cacheType, gasStorageHour, accountID)    
    if 'Error' in tx_hash:
        print(tx_hash)
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
            print('Job\'s index is ' + str(logs[0].args['index']))
            break
