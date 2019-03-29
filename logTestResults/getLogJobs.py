#!/usr/bin/env python3

import sys, asyncio, time, os, subprocess
from web3.auto import w3
from dotenv import load_dotenv
from os.path import expanduser
home = expanduser("~")
sys.path.insert(1, os.path.join(sys.path[0], '..'))
import lib
from imports import connectEblocBroker
from imports import getWeb3

sys.path.insert(0, './contractCalls')
from contractCalls.getJobInfo import getJobInfo

def getEbloBroker():
    from imports import connectEblocBroker
    return connectEblocBroker()

web3        = getWeb3()
eBlocBroker = getEbloBroker()

ipfsFlag = 0

def getLogJobs(clusterAddress, fromBlock):
    print('clusterAddress:' + clusterAddress + '\n')
    myFilter = eBlocBroker.events.LogReceipt.createFilter(
        fromBlock=int(fromBlock),
        argument_filters={'clusterAddress': str(clusterAddress)})
    loggedJobs = myFilter.get_all_entries()


    receiptReturned = {}

    for i in range(0, len(loggedJobs)):
        clusterAddress = loggedJobs[i].args['clusterAddress']
        jobKey         = loggedJobs[i].args['jobKey']
        index          = loggedJobs[i].args['index']
        returned       = loggedJobs[i].args['returned']
        receiptReturned[str(clusterAddress) + str(jobKey) + str(index)] = returned

    # ---------------------------------------------------------------------
    myFilter = eBlocBroker.events.LogJob.createFilter(
        fromBlock=int(fromBlock),
        argument_filters={'clusterAddress': str(clusterAddress)})
    loggedJobs = myFilter.get_all_entries()
    sum_    = 0
    counter = 1
    completedCounter = 0

    for i in range(0, len(loggedJobs)):
        clusterAddress = loggedJobs[i].args['clusterAddress']
        jobKey         = loggedJobs[i].args['jobKey']
        index          = loggedJobs[i].args['index']
        # print(loggedJobs[i])
        # print(loggedJobs[i].args['jobKey'])
        jobInfo = getJobInfo(clusterAddress, jobKey, index, eBlocBroker, web3)
        # print('received: ' +  )
        returned=0
        key=str(clusterAddress) + str(jobKey) + str(index)
        if key in receiptReturned:
            returned=receiptReturned[key]
            #print('returned:' + str(receiptReturned[key]))
        #else:
        #    print('returned:0')

        gained=0
        if lib.inv_job_state_code[int(jobInfo['status'])] == 'COMPLETED':
            #print('gained: ' + str(jobInfo['received'] - returned))
            gained=jobInfo['received'] - returned
            sum_+=gained
            completedCounter+=1
        #else:
        #   print('gained:0')
        
        print(str(counter) + ' | ' + loggedJobs[i].args['jobKey'] + ' ' + str(loggedJobs[i].args['index']) +
          ' ' + lib.inv_job_state_code[int(jobInfo['status'])] + ' ' + str(jobInfo['received']) + ' ' + str(returned) + ' ' + str(gained))       

        if ipfsFlag == 1 and lib.inv_job_state_code[int(jobInfo['status'])] == "COMPLETED":
            subprocess.run(['ipfs', 'get', loggedJobs[i].args['jobKey'],  '--output=ipfsHashes/' + loggedJobs[i].args['jobKey']])
            
        counter+=1
    # print('------------------------------------------------------------------------------------------------------------')
    print("TOTAL_GAINED: " + str(sum_))
    print(str(completedCounter) + "/" + str(counter-1))

if __name__ == '__main__':
    if len(sys.argv) == 3:
        clusterAddress = str(sys.argv[1])
        fromBlock      = int(sys.argv[2])
    else:
        load_dotenv(os.path.join(home + '/.eBlocBroker', '.env')) # Load .env from the given path
        clusterAddress=os.getenv("CLUSTER_ID")
        fromBlock=2215127

    print(fromBlock)    
    getLogJobs(clusterAddress, fromBlock)
