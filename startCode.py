#!/usr/bin/env python

import sys, lib, time, subprocess
from imports import connectEblocBroker
from imports import getWeb3
from contractCalls.setJobStatus import setJobStatus

web3        = getWeb3()
eBlocBroker = connectEblocBroker(web3)

def startCall(jobKey, index, jobID): 
   statusID = str(lib.job_state_code['RUNNING'])
   # cmd: scontrol show job jobID | grep 'StartTime'| grep -o -P '(?<=StartTime=).*(?= E)'
   p1 = subprocess.Popen(['scontrol', 'show', 'job', jobID], stdout=subprocess.PIPE)
   p2 = subprocess.Popen(['grep', 'StartTime'], stdin=p1.stdout, stdout=subprocess.PIPE)
   p1.stdout.close()
   p3 = subprocess.Popen(['grep', '-o', '-P', '(?<=StartTime=).*(?= E)'], stdin=p2.stdout,stdout=subprocess.PIPE)
   p2.stdout.close()
   date      = p3.communicate()[0].decode('utf-8').strip()
   # cmd: date -d 2018-09-09T18:38:29 +"%s"
   startTime = subprocess.check_output(['date', '-d', date, "+'%s'"]).strip().decode('utf-8').replace("'","")
   
   txFile = open(lib.LOG_PATH + '/transactions/' + lib.CLUSTER_ID + '.txt', 'a')        
   txFile.write(lib.EBLOCPATH + "/contractCalls/setJobStatus.py" + ' ' + jobKey + ' ' + index + ' ' + statusID + ' ' + startTime + '\n')    
   time.sleep(0.25)   
   for attempt in range(10):
       txHash = setJobStatus(jobKey, index, statusID, startTime, eBlocBroker, web3)
       if txHash == "notconnected" or txHash == "":
           txFile.write(jobKey + "_" + index + "| Try: " + str(attempt) + " " + txHash + '\n')
           time.sleep(15)
       else: # success
           break
   else: # we failed all the attempts - abort
       sys.exit()
           
   txFile.write(jobKey + '_' + index + '| Tx: ' + txHash + '| setJobStatus_started' +  ' ' + startTime + '\n') 
   txFile.close() 

if __name__ == '__main__':
   jobKey   = sys.argv[1] 
   index    = sys.argv[2] 
   jobID    = sys.argv[3] 
   
   startCall(jobKey, index, jobID)
