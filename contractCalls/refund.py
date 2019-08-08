#!/usr/bin/env python3

import os, sys
from dotenv  import load_dotenv
from imports import connectEblocBroker, getWeb3
from isRequesterExist import isRequesterExist
from os.path import expanduser
home = expanduser("~")

load_dotenv(os.path.join(home + '/.eBlocBroker/', '.env')) # Load .env from the given path

web3        = getWeb3()
eBlocBroker = connectEblocBroker(web3)
PROVIDER_ID  = web3.toChecksumAddress(os.getenv("PROVIDER_ID"))

if __name__ == '__main__': 
    if len(sys.argv) == 4: 
        providerAddress = web3.toChecksumAddress(str(sys.argv[1])) 
        blockReadFrom, coreNumber, priceCoreMin, priceDataTransfer = eBlocBroker.call().getProviderInfo(providerAddress) 
        my_filter = eBlocBroker.eventFilter('LogProvider',{'fromBlock':int(blockReadFrom),'toBlock':int(blockReadFrom) + 1})
        _key  = str(sys.argv[2])
        index = int(sys.argv[3])        
    else: 
        providerAddress = web3.toChecksumAddress('0x57b60037B82154eC7149142c606bA024fBb0f991')
        _key            = 'QmXFVGtxUBLfR2cYPNQtUjRxMv93yzUdej6kYwV1fqUD3U'  # Long Sleep Job
        index           = 3

    if not eBlocBroker.functions.isProviderExists(providerAddress).call():
       print("Requested provider's Ethereum Address (" + providerAddress + ") does not exist.")
       sys.exit() 
          
    fromAccount = PROVIDER_ID
    fromAccount = web3.toChecksumAddress(fromAccount)    
    if not eBlocBroker.functions.isRequesterExists(fromAccount).call(): 
       print("Requested requester's Ethereum Address (" + fromAccount + ") does not exist.")
       sys.exit() 
      
    tx = eBlocBroker.transact({"from": fromAccount, "gas": 4500000}).refund(providerAddress, _key, index) 
    print('Tx_hash: ' + tx.hex()) 
