#!/usr/bin/env python3

import os, sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from imports import connectEblocBroker
from imports import getWeb3
from contractCalls.isUserExist import isUserExist

web3        = getWeb3()
eBlocBroker = connectEblocBroker(web3)

if __name__ == '__main__': #{
    if len(sys.argv) == 10: #{
        clusterAddress = web3.toChecksumAddress(str(sys.argv[1])) 
        blockReadFrom, coreNumber, pricePerMin = eBlocBroker.call().getClusterInfo(clusterAddress) 
        my_filter = eBlocBroker.eventFilter('LogCluster',{'fromBlock':int(blockReadFrom),'toBlock':int(blockReadFrom) + 1})
        jobKey         = str(sys.argv[2]) 
        coreNum        = int(sys.argv[3]) 
        coreGasDay     = int(sys.argv[4]) 
        coreGasHour    = int(sys.argv[5]) 
        coreGasMin     = int(sys.argv[6]) 
        jobDescription = str(sys.argv[7]) 
        storageType    = int(sys.argv[8]) 
        accountID      = int(sys.argv[9]) 
    #}
    else: #{
        # USER Inputs ================================================================
        clusterAddress = web3.toChecksumAddress("0x4e4a0750350796164D8DefC442a712B7557BF282")
        jobKey         = "105948189774037812791543685388909450727"  # Long Sleep Job
        index          = 0
        accountID      = 0 
        # =============================================================================
    #}

    if not eBlocBroker.functions.isClusterExist(clusterAddress).call(): #{
       print("Requested cluster's Ethereum Address (" + clusterAddress + ") does not exist.")
       sys.exit() 
    #}
    
    fromAccount = web3.eth.accounts[accountID] 
    fromAccount = web3.toChecksumAddress(fromAccount) 
    if not eBlocBroker.functions.isUserExist(fromAccount).call(): #{
       print("Requested user's Ethereum Address (" + fromAccount + ") does not exist.")
       sys.exit() 
    #}
      
    tx = eBlocBroker.transact({"from": web3.eth.accounts[accountID], "gas": 4500000}).cancelRefund(clusterAddress, jobKey, index) 
    print('Tx: ' + tx.hex()) 
#}
