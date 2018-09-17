#!/usr/bin/env python

'''
asynchronous polling: http://web3py.readthedocs.io/en/latest/filters.html#examples-listening-for-events
'''

import sys, asyncio, time
from web3.auto import w3

# -----------------
def handle_event(event):

    # print(event.blockNumber)
    # print(event.args.clusterAddress)
    # print(event.args.jobKey)
    # print(event.args.index)
    # print(event.args.storageID)

    print(event)

def log_loop(event_filter, poll_interval): #{
    flag = 1 
    for event in event_filter.get_all_entries():
        handle_event(event)
        flag = 0 
    
    while True and flag: #{
        for event in event_filter.get_new_entries():
            handle_event(event)
            flag = 0 
        if flag == 0:
            break 
        time.sleep(poll_interval)              
    #}
#}    

def logJob(eBlocBroker=None): #{
   if eBlocBroker is None: #{
       import os 
       sys.path.insert(1, os.path.join(sys.path[0], '..')) 
       from imports import connectEblocBroker
       eBlocBroker = connectEblocBroker()
   #}
   
   loggedJobs = runLogJob(fromBlock, clusterAddress, eBlocBroker) 

   # print(myFilter.filter_params)
   if len(loggedJobs) == 0:
       log_loop(myFilter, 2)
   else: #{
       # print(myFilter.get_all_entries())
       for i in range(0, len(loggedJobs)):
           print(loggedJobs[i]) 
           print(loggedJobs[i]['blockNumber']) 
           print(loggedJobs[i].args['clusterAddress']) 
           print(loggedJobs[i].args['jobKey']) 
           print(loggedJobs[i].args['index']) 
           print(loggedJobs[i].args['storageID']) 
           print(loggedJobs[i].args['desc']) 
   #}    
#}
# -----------------

def getEbloBroker(): #{
    import os 
    sys.path.insert(1, os.path.join(sys.path[0], '..')) 
    from imports import connectEblocBroker
    return connectEblocBroker()
#}

def logReturn(event_filter, poll_interval): #{    
    while True: #{
        loggedJobs = event_filter.get_new_entries() 
        if len(loggedJobs) > 0:
            return loggedJobs         
        time.sleep(poll_interval)              
    #}
#}    

def runLogJob(fromBlock, clusterAddress, eBlocBroker=None): #{
   if eBlocBroker is None: #{
       eBlocBroker = getEbloBroker()
   #}

   myFilter = eBlocBroker.events.LogJob.createFilter(
       fromBlock=int(fromBlock),       
       argument_filters={'clusterAddress': str(clusterAddress)}
   )    
   loggedJobs = myFilter.get_all_entries() 

   if len(loggedJobs) > 0:       
       return loggedJobs 
   else:
       return logReturn(myFilter, 2) 
#}

def runLogCancelRefund(fromBlock, clusterAddress, eBlocBroker=None): #{
   if eBlocBroker is None: #{
       eBlocBroker = getEbloBroker()
   #}
   myFilter = eBlocBroker.events.LogCancelRefund.createFilter(
       fromBlock=int(fromBlock),       
       # argument_filters={'clusterAddress': str(clusterAddress)} #TODO: uncomment
   )
   loggedJobs = myFilter.get_all_entries() 

   if len(loggedJobs) > 0:       
       return loggedJobs 
   else:
       return logReturn(myFilter, 2) 
#}

if __name__ == '__main__': #{
   if len(sys.argv) == 2: #{
        fromBlock      = int(sys.argv[1]) 
        clusterAddress = str(sys.argv[2]) # Only obtains jobs that are submitted to the cluster.
   #}
   else: #{
       fromBlock      = 954795 
       clusterAddress = '0x4e4a0750350796164d8defc442a712b7557bf282'
   #}   

   loggedJobs = runLogJob(fromBlock, clusterAddress)
   for i in range(0, len(loggedJobs)):
           print(loggedJobs[i])
           print(loggedJobs[i]['blockNumber'])
           print(loggedJobs[i].args['clusterAddress'])
           print(loggedJobs[i].args['jobKey'])
           print(loggedJobs[i].args['index'])
           print(loggedJobs[i].args['storageID'])
           print(loggedJobs[i].args['desc'])
   #}   
#}


