#!/usr/bin/env python3

'''
asynchronous polling: http://web3py.readthedocs.io/en/latest/filters.html#examples-listening-for-events
'''

import sys, asyncio, time
from web3.auto import w3

def getEbloBroker():
    import os 
    from imports import connectEblocBroker
    return connectEblocBroker()

def logReturn(event_filter, poll_interval):
    while True:
        loggedJobs = event_filter.get_new_entries() 
        if len(loggedJobs) > 0:
            return loggedJobs         
        time.sleep(poll_interval)              

def runLogJob(fromBlock, providerAddress, eBlocBroker=None): 
   if eBlocBroker is None: 
       eBlocBroker = getEbloBroker()
   myFilter = eBlocBroker.events.LogJob.createFilter(
       fromBlock=int(fromBlock),       
       argument_filters={'provider': str(providerAddress)}
   )    
   loggedJobs = myFilter.get_all_entries() 
   if len(loggedJobs) > 0:       
       return loggedJobs 
   else:
       return logReturn(myFilter, 2) 

def runLogCancelRefund(fromBlock, providerAddress, eBlocBroker=None):
    if eBlocBroker is None: 
        eBlocBroker = getEbloBroker()
        
    myFilter = eBlocBroker.events.LogRefund.createFilter(
        fromBlock=int(fromBlock),       
        argument_filters={'provider': str(providerAddress)})
    loggedCancelledJobs = myFilter.get_all_entries() 
    if len(loggedCancelledJobs) > 0:       
        return loggedCancelledJobs
    else:
        return logReturn(myFilter, 2) 

def runSingleLogJob(fromBlock, jobKey, transactionHash, eBlocBroker=None): 
   if eBlocBroker is None: 
       eBlocBroker = getEbloBroker()

   myFilter = eBlocBroker.events.LogJob.createFilter(
       fromBlock=int(fromBlock),       
       # argument_filters={'jobKey': str(jobKey)}
   )    
   loggedJobs = myFilter.get_all_entries() 

   if len(loggedJobs) > 0:
       for i in range(0, len(loggedJobs)):
           if loggedJobs[i]['transactionHash'].hex() == transactionHash:
               return loggedJobs[i]['index']
   else:
       return logReturn(myFilter, 2) 

if __name__ == '__main__': 
   if len(sys.argv) == 2: 
        fromBlock       = int(sys.argv[1]) 
        providerAddress = str(sys.argv[2]) # Only obtains jobs that are submitted to the provider.
   else:
       fromBlock       = 954795 
       providerAddress = '0x4e4a0750350796164d8defc442a712b7557bf282'

   loggedJobs = runLogJob(fromBlock, providerAddress)
   for i in range(0, len(loggedJobs)):
           print(loggedJobs[i])
           print('Tx_hash: ' + loggedJobs[i]['transactionHash'].hex() )
           print('blockNumber: ' + str(loggedJobs[i]['blockNumber']))
           print('providerAddress: ' + loggedJobs[i].args['provider'])

           print(loggedJobs[i].args['jobKey'])           

           print('jobKey: ' + loggedJobs[i].args['jobKey'])
           print('index: ' + str(loggedJobs[i].args['index']))
           print('storageID: ' + str(loggedJobs[i].args['storageID']))           
           print('------------------------------------------------------------------------------------------------------------')
