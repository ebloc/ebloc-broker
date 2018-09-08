#!/usr/bin/env python

import sys, os, lib, _thread

from imports import connectEblocBroker
from imports import getWeb3
from contractCalls.blockNumber            import blockNumber
from contractCalls.getDeployedBlockNumber import getDeployedBlockNumber

web3        = getWeb3() 
eBlocBroker = connectEblocBroker() 

cancelledJobsReadFromPath = lib.CANCEL_JOBS_READ_FROM_FILE 
os.environ['cancelledJobsReadFromPath'] = cancelledJobsReadFromPath 

def log(strIn, color=''): #{
   '''
   if color != '':
      print(stylize(strIn, fg(color))) 
   else:
      print(strIn)
   '''
   txFile = open(lib.LOG_PATH + '/cancelledJobsLog.out', 'a') 
   txFile.write(strIn + "\n") 
   txFile.close()    
#}

f = open(lib.CANCEL_BLOCK_READ_FROM_FILE, 'r')
cancelBlockReadFromLocal = f.read().rstrip('\n') 
f.close() 

if not cancelBlockReadFromLocal.isdigit():
    cancelBlockReadFromLocal = getDeployedBlockNumber(eBlocBroker) 
    
    os.environ['cancelBlockReadFromLocal'] = cancelBlockReadFromLocal 
else:
    os.environ['cancelBlockReadFromLocal'] = cancelBlockReadFromLocal 

log('Waiting cancelled jobs from :' + cancelBlockReadFromLocal)

maxVal = 0        
while True: #{
    # Waits here until new job cancelled into the cluster
    lib.contractCallNode('eBlocBroker.LogCancelRefund($cancelBlockReadFromLocal, \'$cancelledJobsReadFromPath\')')   

    if os.path.isfile(cancelledJobsReadFromPath): #{ Waits until generated file on log is completed       
        cancelledJobs = set() # holds lines already seen
        for line in open(cancelledJobsReadFromPath, "r"):
            if line not in cancelledJobs: # not a duplicate
                cancelledJobs.add(line)

    cancelledJobs= sorted(cancelledJobs) 
    for e in cancelledJobs: #{
        cancelledJob = e.rstrip('\n').split(' ') 
        os.environ['jobKey'] = cancelledJob[2] 
        os.environ['index']  = cancelledJob[3]         
        log(cancelledJob[0] + ' ' + cancelledJob[1] + ' ' + cancelledJob[2] + ' ' + cancelledJob[3]  )

        if int(cancelledJob[0]) > int(maxVal):
            maxVal = cancelledJob[0]

        jobName = os.popen('echo ~/.eBlocBroker/ipfsHashes/$jobKey\_$index/JOB_TO_RUN/$jobKey\*$index*sh | xargs -n 1 basename').read()
        os.environ['jobName']  = jobName         
        res = os.popen('sacct --name $jobName | tail -n1 | awk \'{print $1}\'').read().rstrip('\n') 
        
        if res.isdigit():
            log('JobID: ' + res + ' is cancelled.')
            os.popen('scancel ' + res).read()         
        
        #}

    if int(maxVal) != 0: #{ 
        f_blockReadFrom = open(lib.CANCEL_BLOCK_READ_FROM_FILE, 'w')  # Updates the latest read block number      
        f_blockReadFrom.write(str(int(maxVal) + 1) + '\n')  
        f_blockReadFrom.close() 
        cancelBlockReadFromLocal = str(int(maxVal) + 1) 
        os.environ['cancelBlockReadFromLocal'] = cancelBlockReadFromLocal 
        log('Waiting cancelled jobs from :' + cancelBlockReadFromLocal)
    #}
    else:
        currentBlockNumber = blockNumber(web3) 
        
        f_blockReadFrom = open(lib.CANCEL_BLOCK_READ_FROM_FILE, 'w')  # Updates the latest read block number      
        f_blockReadFrom.write(str(currentBlockNumber) + '\n')  
        f_blockReadFrom.close() 
        os.environ['cancelBlockReadFromLocal'] = currentBlockNumber 
        log('Waiting cancelled jobs from :' + currentBlockNumber)
#}
