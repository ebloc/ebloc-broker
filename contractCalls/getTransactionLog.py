#!/usr/bin/env python

import sys, time, os
sys.path.insert(1, os.path.join(sys.path[0], '..'))
import lib

from imports import getWeb3
from imports import connectEblocBroker

web3 = getWeb3()
eBlocBroker = connectEblocBroker(web3)

def processLog(log): #{
    print(log)
    print('-----------')
    print(log[0].args['index'])
#}

if __name__ == '__main__': #{
    if len(sys.argv) == 2:
        tx_hash = str(sys.argv[1])
        event   = 'LogJob' 
    else:
        tx_hash = '0xdf9ead46baefd6774b230a7286d510bceec04fb33200c9ac9b6934e5cf46f6c7'
        event   = 'LogJob' 

    receipt = web3.eth.getTransactionReceipt(tx_hash)

    if event is 'LogJob':
        logs = eBlocBroker.events.LogJob().processReceipt(receipt)
        processLog(logs)    
#}
