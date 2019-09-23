#!/usr/bin/env python3

import os, sys, traceback
from dotenv  import load_dotenv
from imports import connectEblocBroker, getWeb3
from isRequesterExist import isRequesterExist
from os.path import expanduser
home = expanduser("~")

load_dotenv(os.path.join(home + '/.eBlocBroker/', '.env')) # Load .env from the given path

w3          = getWeb3()
eBlocBroker = connectEblocBroker(w3)
PROVIDER_ID = w3.toChecksumAddress(os.getenv("PROVIDER_ID")) # TODO: should be requester_id

def refund(provider, _key, index):
    if not eBlocBroker.functions.isProviderExists(provider).call():
       print("Requested provider's Ethereum Address (" + provider + ") does not exist.")
       sys.exit() 
          
    fromAccount = PROVIDER_ID
    fromAccnount = w3.toChecksumAddress(fromAccount)    
    if not eBlocBroker.functions.isRequesterExists(fromAccount).call(): 
       print("Requested requester's Ethereum Address (" + fromAccount + ") does not exist.")
       sys.exit()
       
    try:
        gasLimit = 4500000
        tx = eBlocBroker.transact({"from": fromAccount, "gas": gasLimit}).refund(provider, _key, index)
    except Exception:
        return False, traceback.format_exc()
    
    return True, tx.hex()
    
if __name__ == '__main__': 
    if len(sys.argv) == 4: 
        provider = w3.toChecksumAddress(str(sys.argv[1])) 
        blockReadFrom, coreNumber, priceCoreMin, priceDataTransfer = eBlocBroker.call().getProviderInfo(provider) 
        my_filter = eBlocBroker.eventFilter('LogProvider',{'fromBlock':int(blockReadFrom),'toBlock':int(blockReadFrom) + 1})
        _key  = str(sys.argv[2])
        index = int(sys.argv[3])        
    else: 
        provider = w3.toChecksumAddress('0x57b60037B82154eC7149142c606bA024fBb0f991')
        _key     = 'QmXFVGtxUBLfR2cYPNQtUjRxMv93yzUdej6kYwV1fqUD3U'  # Long Sleep Job
        index    = 3

    status, result = refund(provider, _key, index)
    
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

