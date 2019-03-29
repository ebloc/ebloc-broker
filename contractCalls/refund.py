#!/usr/bin/env python3

import os, sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from dotenv  import load_dotenv
from imports import connectEblocBroker
from imports import getWeb3
from contractCalls.isUserExist import isUserExist
from os.path import expanduser
home = expanduser("~")

load_dotenv(os.path.join(home + '/.eBlocBroker/', '.env')) # Load .env from the given path

web3        = getWeb3()
eBlocBroker = connectEblocBroker(web3)
CLUSTER_ID  = web3.toChecksumAddress(os.getenv("CLUSTER_ID"))

if __name__ == '__main__': 
    if len(sys.argv) == 4: 
        clusterAddress = web3.toChecksumAddress(str(sys.argv[1])) 
        blockReadFrom, coreNumber, priceCoreMin, priceDataTransfer = eBlocBroker.call().getClusterInfo(clusterAddress) 
        my_filter = eBlocBroker.eventFilter('LogCluster',{'fromBlock':int(blockReadFrom),'toBlock':int(blockReadFrom) + 1})
        jobKey = str(sys.argv[2])
        index  = int(sys.argv[3])        
    else: 
        # USER Inputs =======================================================================
        clusterAddress = web3.toChecksumAddress('0x57b60037B82154eC7149142c606bA024fBb0f991')
        jobKey         = 'QmXFVGtxUBLfR2cYPNQtUjRxMv93yzUdej6kYwV1fqUD3U'  # Long Sleep Job
        index          = 3
        # ===================================================================================

    if not eBlocBroker.functions.isClusterExist(clusterAddress).call():
       print("Requested cluster's Ethereum Address (" + clusterAddress + ") does not exist.")
       sys.exit() 
          
    fromAccount = CLUSTER_ID
    fromAccount = web3.toChecksumAddress(fromAccount)    
    if not eBlocBroker.functions.isUserExist(fromAccount).call(): 
       print("Requested user's Ethereum Address (" + fromAccount + ") does not exist.")
       sys.exit() 
      
    tx = eBlocBroker.transact({"from": fromAccount, "gas": 4500000}).refund(clusterAddress, jobKey, index) 
    print('Tx_hash: ' + tx.hex()) 
