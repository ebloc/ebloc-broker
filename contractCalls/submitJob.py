#!/usr/bin/env python

import os, sys, time
sys.path.insert(1, os.path.join(sys.path[0], '..'))
import lib
from imports import connectEblocBroker
from imports import getWeb3

web3        = getWeb3()
eBlocBroker = connectEblocBroker(web3)


def submitJob(clusterAddress, jobKey, coreNum, coreGasDay, coreGasHour, coreGasMin, jobDescription, storageID, accountID): #{
    clusterAddress = web3.toChecksumAddress(clusterAddress)  #POA
    # clusterAddress = web3.toChecksumAddress("0x75a4c787c5c18c587b284a904165ff06a269b48c")  #POW        
    blockReadFrom, coreNumber, pricePerMin = eBlocBroker.functions.getClusterInfo(clusterAddress).call() 
    my_filter = eBlocBroker.eventFilter('LogCluster',{'fromBlock':int(blockReadFrom),'toBlock':int(blockReadFrom) + 1})    

    if not eBlocBroker.functions.isClusterExist(clusterAddress).call(): #{
       return "Requested cluster's Ethereum Address \"" + clusterAddress + "\" does not exist."
    #}
    
    fromAccount = web3.eth.accounts[accountID] 
    fromAccount = web3.toChecksumAddress(fromAccount) 

    blockReadFrom, orcid = eBlocBroker.functions.getUserInfo(fromAccount).call() 
    if not eBlocBroker.functions.isUserExist(fromAccount).call(): #{
       return "Requested user's Ethereum Address \"" + fromAccount + "\" does not exist."
    #}

    if str(eBlocBroker.functions.isOrcIdVerified(orcid).call()) == '0': #{
       return 'User\'s orcid: ' + orcid + ' is not verified.'
    #}    

    if storageID == 0 or storageID == 2: #{
       lib.isIpfsOn()
       strVal = my_filter.get_all_entries()[0].args['ipfsAddress'] 
       output = os.popen('ipfs swarm connect ' + strVal).read() 
       print("Trying to connect into: " + strVal) 
       if 'success' in output:
          print(output)
    #}
    
    coreMinuteGas = coreGasMin + coreGasHour * 60 + coreGasDay * 1440 
    msgValue      = coreNum * pricePerMin * coreMinuteGas 
    
    if (storageID == 0 and len(jobKey) != 46) or (storageID == 2 and len(jobKey) != 46) or (storageID == 4 and len(jobKey) != 33): #{
       return "jobKey's length does not match with its original length. Please check your jobKey."
    #}

    gasLimit = 4500000  
    if coreNum <= coreNumber and len(jobDescription) < 128 and int(storageID) < 5 and len(jobKey) <= 64 and coreMinuteGas != 0: #{
       tx = eBlocBroker.transact({"from": fromAccount, "value": msgValue, "gas": gasLimit}).submitJob(clusterAddress, jobKey, coreNum, jobDescription, coreMinuteGas, storageID) 
       return 'Tx: ' + tx.hex()
       #print('Value: ' + str(msgValue)) 
       #print(clusterAddress + " " + jobKey + " " + str(coreNum) + " " + jobDescription + " " + str(coreMinuteGas) + " " + str(storageID))
    #}
#}

if __name__ == '__main__': #{
    if len(sys.argv) == 10: #{
        clusterAddress = str(sys.argv[1])
        jobKey         = str(sys.argv[2]) 
        coreNum        = int(sys.argv[3]) 
        coreGasDay     = int(sys.argv[4]) 
        coreGasHour    = int(sys.argv[5]) 
        coreGasMin     = int(sys.argv[6]) 
        jobDescription = str(sys.argv[7]) 
        storageID      = int(sys.argv[8]) 
        accountID      = int(sys.argv[9])
    #}
    else: #{
        # USER Inputs ================================================================
        clusterAddress = '0x4e4a0750350796164D8DefC442a712B7557BF282'        
        #jobKey         = "3d8e2dc2-b855-1036-807f-9dbd8c6b1579=folderName" 
        jobKey         = "QmRsaBEGcqxQcJbBxCi1LN9iz5bDAGDWR6Hx7ZvWqgqmdR"
        # jobKey         = "QmRsaBEGcqxQcJbBxCi1LN9iz5bDAGDWR6Hx7ZvWqgqmdR"  # Long Sleep Job.
        # jobKey         = "QmefdYEriRiSbeVqGvLx15DKh4WqSMVL8nT4BwvsgVZ7a5"  #"1-R0MoQj7Xfzu3pPnTqpfLUzRMeCTg6zG"
        coreNum        = 1 
        coreGasDay     = 0 
        coreGasHour    = 0 
        coreGasMin     = 1 
        jobDescription = "Science" 
        storageID      = 0 
        accountID      = 0        
        # =============================================================================
    #}
    ret = submitJob(clusterAddress, jobKey, coreNum, coreGasDay, coreGasHour, coreGasMin, jobDescription, storageID, accountID)
    print(ret)
#}
