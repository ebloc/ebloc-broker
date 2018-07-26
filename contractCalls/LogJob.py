#!/usr/bin/env python

'''
asynchronous polling: http://web3py.readthedocs.io/en/latest/filters.html#examples-listening-for-events
'''

from imports import *

from web3.auto import w3
import asyncio
   
def handle_event(event):
    '''
    print(event.blockNumber)
    print(event.args.clusterAddress)
    print(event.args.jobKey)
    print(event.args.index)
    print(event.args.storageID)
    '''
    print(event)

def log_loop(event_filter, poll_interval): #{
    flag = 1;
    for event in event_filter.get_all_entries():
        handle_event(event)
        flag = 0;
    
    while True and flag: #{
        for event in event_filter.get_new_entries():
            handle_event(event)
            flag = 0;
        if flag == 0:
            break;
        time.sleep(poll_interval)              
    #}
#}    

def log_ret(event_filter, poll_interval): #{    
    while True: #{
        loggedJobs = event_filter.get_new_entries();
        if len(loggedJobs) > 0:
            return loggedJobs;        
        time.sleep(poll_interval)              
    #}
#}    

def run(fromBlock, clusterAddress): #{
   myFilter = eBlocBroker.events.LogJob.createFilter(
       fromBlock=int(fromBlock),       
       argument_filters={'clusterAddress': str(clusterAddress)}
   );
   
   loggedJobs = myFilter.get_all_entries();

   if len(loggedJobs) > 0:       
       return loggedJobs;
   else:
       return log_ret(myFilter, 2);
#}
                 
if __name__ == '__main__': #{
   if len(sys.argv) == 2:
        fromBlock      = int(sys.argv[1]);
        clusterAddress = str(sys.argv[2]); # Only obtains jobs that are submitted to the cluster.
   else:
        fromBlock      = 857060; #875682; 
        clusterAddress = '0x4e4a0750350796164D8DefC442a712B7557BF282';

   loggedJobs = run(fromBlock, clusterAddress);

   # print(myFilter.filter_params)
   if len(loggedJobs) == 0:       
       log_loop(myFilter, 2)
   else: #{
       # print(myFilter.get_all_entries())
       for i in range(0, len(loggedJobs)):
           print(loggedJobs[i]);
           print(loggedJobs[i]['blockNumber']);
           print(loggedJobs[i].args['clusterAddress']);
           print(loggedJobs[i].args['jobKey']);
           print(loggedJobs[i].args['index']);           
           print(loggedJobs[i].args['storageID']);           
           print(loggedJobs[i].args['desc']);                      
   #}

#}

