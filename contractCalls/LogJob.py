#!/usr/bin/env python

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
   
if __name__ == '__main__': #{    
   myFilter = eBlocBroker.events.LogJob.createFilter(
       fromBlock=857060
       # , argument_filters={'clusterAddress': '0x4e4a0750350796164D8DefC442a712B7557BF282'}
   )   
   print(myFilter.get_all_entries())
   # print(myFilter.filter_params)
   # print(eBlocBroker.events.LogJob.abi)
   # log_loop(myFilter, 2)
#}

