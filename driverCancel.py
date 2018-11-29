#!/usr/bin/env python

import sys, os, lib, _thread, time, hashlib, subprocess
sys.path.insert(0, './contractCalls')
import LogJob
from imports import connectEblocBroker
from imports import getWeb3
from contractCalls.blockNumber            import blockNumber
from contractCalls.getDeployedBlockNumber import getDeployedBlockNumber

web3        = getWeb3() 
eBlocBroker = connectEblocBroker() 
testFlag    = False

def log(strIn, color=''): 
   if testFlag: 
      if color != '':
         print(stylize(strIn, fg(color))) 
      else:
         print(strIn)

   txFile = open(lib.LOG_PATH + '/cancelledJobsLog.out', 'a') 
   txFile.write(strIn + "\n") 
   txFile.close()    

with open(lib.CANCEL_BLOCK_READ_FROM_FILE, 'r') as content_file:
   cancelBlockReadFromLocal = content_file.read().strip()

if not cancelBlockReadFromLocal.isdigit():
    cancelBlockReadFromLocal = getDeployedBlockNumber(eBlocBroker)    

log('Waiting cancelled jobs from :' + cancelBlockReadFromLocal)

maxVal = 0
while True: #{
    if testFlag:
       cancelBlockReadFromLocal = 1146520
       
    # Waits here until new job cancelled into the cluster
    loggedJobs = LogJob.runLogCancelRefund(cancelBlockReadFromLocal, lib.CLUSTER_ID, eBlocBroker)

    for e in range(0, len(loggedJobs)): #{
        msg_sender = web3.eth.getTransactionReceipt(loggedJobs[e]['transactionHash'].hex())['from'].lower()
        userName   = hashlib.md5(msg_sender.encode('utf-8')).hexdigest();        
        #print(msg_sender)
        #print(loggedJobs[e])
        #print(userName)
        
        blockNumber = loggedJobs[e]['blockNumber']
        jobKey = loggedJobs[e].args['jobKey']
        index  = loggedJobs[e].args['index']        
        log('blockNumber=' + str(blockNumber) + ' jobKey=' + jobKey + ' index=' + str(index)) 
               
        if blockNumber > maxVal:
           maxVal = blockNumber

        '''
        cmd: sudo su - c6cec9ebdb49fa85449c49251f4a0b9d -c 'jobName=$(echo 200376512531615951349171797788434913951_0/JOB_TO_RUN/200376512531615951349171797788434913951\*0*sh | xargs -n 1 basename); sacct -n -X --format jobid --name $jobName'
        output: 51           231555615+      debug cc6b74f19+          1  COMPLETED      0:0
        '''
        res = subprocess.check_output(['sudo', 'su', '-', userName, '-c',
                                       'jobName=$(echo ' + jobKey + '_' + str(index) + '/JOB_TO_RUN/' + jobKey + '*' + str(index) + '*sh | xargs -n 1 basename);' +
                                       'sacct -n -X --format jobid --name $jobName']).decode('utf-8').split()
        try:
           jobID = res[0]
           print('jobID=' + jobID)
           if jobID.isdigit():
              subprocess.run(['scancel', jobID])
              time.sleep(2) # wait few seconds to cancel the requested job.
              p1 = subprocess.Popen(['scontrol', 'show', 'job', jobID], stdout=subprocess.PIPE)
              #-----------
              p2 = subprocess.Popen(['grep', 'JobState='], stdin=p1.stdout, stdout=subprocess.PIPE)
              p1.stdout.close()
            
              out = p2.communicate()[0].decode('utf-8').strip()
              if 'JobState=CANCELLED' in out:
                 log('JobID=' + jobID + ' is successfully cancelled.')
              else:
                 log('Error: jobID=' + jobID + ' is not cancelled, something went wrong or already cancelled. ' + out)
        except IndexError:
           log('Something went wrong, jobID is returned as None.')
        
                    
    if int(maxVal) != 0:
        f_blockReadFrom = open(lib.CANCEL_BLOCK_READ_FROM_FILE, 'w')  # Updates the latest read block number      
        f_blockReadFrom.write(str(int(maxVal) + 1) + '\n')  
        f_blockReadFrom.close() 
        cancelBlockReadFromLocal = str(int(maxVal) + 1)
        log('---------------------------------------------')
        log('Waiting cancelled jobs from :' + cancelBlockReadFromLocal)
    else:
        currentBlockNumber = blockNumber(web3)         
        f_blockReadFrom = open(lib.CANCEL_BLOCK_READ_FROM_FILE, 'w')  # Updates the latest read block number      
        f_blockReadFrom.write(str(currentBlockNumber) + '\n')  
        f_blockReadFrom.close()
        log('---------------------------------------------')
        log('Waiting cancelled jobs from :' + currentBlockNumber)
    #}
#}
