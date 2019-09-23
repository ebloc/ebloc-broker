#!/usr/bin/env python3

'''
Guide asynchronous polling: http://web3py.readthedocs.io/en/latest/filters.html#examples-listening-for-events
'''

import sys, asyncio, time, lib
from web3.auto import w3
from imports   import connect, connectEblocBroker, getWeb3
import binascii, base58


def logReturn(event_filter, poll_interval):
    while True:
        loggedJobs = event_filter.get_new_entries() 
        if len(loggedJobs) > 0:
            return loggedJobs         
        time.sleep(poll_interval)              

def runLogJob(fromBlock, provider, eBlocBroker=None, w3=None):
    eBlocBroker, w3 = connect(eBlocBroker, w3)
    if eBlocBroker is None or w3 is None:
        return

    event_filter = eBlocBroker.events.LogJob.createFilter(fromBlock=int(fromBlock), toBlock="latest", argument_filters={'provider': str(provider)})
    loggedJobs = event_filter.get_all_entries()
    
    if len(loggedJobs) > 0:       
        return loggedJobs 
    else:
        return logReturn(event_filter, 2) 

def runLogCancelRefund(fromBlock, provider, eBlocBroker=None, w3=None):
    eBlocBroker, w3 = connect(eBlocBroker, w3)
    if eBlocBroker is None or w3 is None:
        return
        
    event_filter = eBlocBroker.events.LogRefund.createFilter(fromBlock=int(fromBlock), argument_filters={'provider': str(provider)})
    loggedCancelledJobs = event_filter.get_all_entries() 
    if len(loggedCancelledJobs) > 0:       
        return loggedCancelledJobs
    else:
        return logReturn(event_filter, 2) 

def runSingleLogJob(fromBlock, jobKey, transactionHash, eBlocBroker=None, w3=None):
    eBlocBroker, w3 = connect(eBlocBroker, w3)
    if eBlocBroker is None or w3 is None:
        return
        
    event_filter = eBlocBroker.events.LogJob.createFilter(fromBlock=int(fromBlock), argument_filters={'provider': str(provider)})    
    loggedJobs = event_filter.get_all_entries() 

    if len(loggedJobs) > 0:
        for i in range(0, len(loggedJobs)):
            if loggedJobs[i]['transactionHash'].hex() == transactionHash:
                return loggedJobs[i]['index']
    else:
        return logReturn(event_filter, 2) 

if __name__ == '__main__': 
    if len(sys.argv) == 3: 
        fromBlock = int(sys.argv[1]) 
        provider  = str(sys.argv[2]) # Only obtains jobs that are submitted to the provider.
    else:
        fromBlock = 3070724
        provider  = '0x57b60037b82154ec7149142c606ba024fbb0f991'
        print('here')
       
    loggedJobs = runLogJob(fromBlock, provider)
    for i in range(0, len(loggedJobs)):
        # print(loggedJobs[i])
        storageID = loggedJobs[i].args['storageID']
        '''
        if lib.StorageID.IPFS.value == storageID or lib.storageID.IPFS_MINILOCK.value == storageID:
            jobKey = lib.convertBytes32ToIpfs(loggedJobs[i].args['jobKey'])
        else:
            jobKey = loggedJobs[i].args['jobKey']
        '''
                         
        print('tx_hash: ' + loggedJobs[i]['transactionHash'].hex() )
        print('blockNumber: ' + str(loggedJobs[i]['blockNumber']))
        print('provider: '  + loggedJobs[i].args['provider'])              
        print('jobKey: '    + loggedJobs[i].args['jobKey'])
        print('index: '     + str(loggedJobs[i].args['index']))
        print('storageID: ' + str(lib.StorageID(storageID).name))       
        print('cacheType: ' + str(lib.CacheType(loggedJobs[i].args['cacheType']).name))
        print('received: ' + str(loggedJobs[i].args['received']))
        for i in range(0, len(loggedJobs[i].args['sourceCodeHash'])):
            sourceCodeHash = loggedJobs[i].args['sourceCodeHash'][i]
            print('sourceCodeHash[' + str(i) + ']: ' +  lib.convertBytes32ToIpfs(sourceCodeHash))
            
        print('------------------------------------------------------------------------------------------------------------')

# bytes32[] sourceCodeHash,
# uint8 cacheType,
# uint received);
       
