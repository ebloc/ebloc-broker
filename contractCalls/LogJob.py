#!/usr/bin/env python

import os, json, sys, time
from web3 import Web3
from web3.providers.rpc import HTTPProvider
sys.path.insert(1, os.path.join(sys.path[0], '..')); import constants
os.chdir(sys.path[0]);

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
def main():
   ''' main function

   ...
   '''
        
   web3 = Web3(HTTPProvider('http://localhost:' + str(constants.RPC_PORT)))

   if not web3.isConnected(): #{
      print('notconnected')
      sys.exit()
   #}
   
   fileAddr        = open("address.json", "r")
   contractAddress = fileAddr.read().replace("\n", "")

   with open('abi.json', 'r') as abi_definition:
      abi = json.load(abi_definition)
   
   contractAddress = web3.toChecksumAddress(contractAddress);    
   eBlocBroker     = web3.eth.contract(contractAddress, abi=abi);

   blockReadFrom = 1899690;     
   myFilter = eBlocBroker.events.LogJob.createFilter(
       fromBlock=blockReadFrom,
       argument_filters={'desc': 'Science'}
   )
   print(myFilter.get_all_entries())
   #print(myFilter.filter_params)
   #print(eBlocBroker.events.LogJob.abi)
   # log_loop(myFilter, 2)

   print('---')
   print(web3.eth.getTransactionReceipt("0x183e1d0a796ecacedb9c5eeb6f84cbf9a198db1554572d6d06d87aedf4c0120b"))
   
if __name__ == '__main__':
    main()

