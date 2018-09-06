#!/usr/bin/env python

import sys, os, lib, time

contractCallPath               = lib.EBLOCPATH + '/contractCalls' 
os.environ['contractCallPath'] = contractCallPath 

def startCall(jobKey, index, jobID): #{
   os.environ['eblocPath'] = lib.EBLOCPATH 
   os.environ['index']     = str(index) 
   os.environ['jobKey']    = jobKey 
   statusId                = str(lib.job_state_code['RUNNING']) 
   os.environ['statusId']  = statusId 
   os.environ['jobID']     = jobID 

   starTime = os.popen('date -d $(scontrol show job $jobID | grep \'StartTime\'| grep -o -P \'(?<=StartTime=).*(?= E)\') +"%s"').read().rstrip('\n') 
   os.environ['starTime']  = starTime 
            
   txFile = open(lib.LOG_PATH + '/transactions/' + lib.CLUSTER_ID + '.txt', 'a') 
   txFile.write(os.popen('echo $contractCallPath/setJobStatus.py $jobKey $index $statusId $starTime').read().rstrip('\n'))    
   time.sleep(0.25) 

   countTry = 0    
   txHash = os.popen('$eblocPath/venv/bin/python3 $contractCallPath/setJobStatus.py $jobKey $index $statusId $starTime').read().rstrip('\n')    
   while txHash == "notconnected" or txHash == "": #{
      if countTry > 10:
         sys.exit() 
      txFile.write(jobKey + "_" + index + "| Try: " + str(countTry) + " " + txHash + '\n') 
      txHash = os.popen('$eblocPath/venv/bin/python3 $contractCallPath/setJobStatus.py $jobKey $index $statusId $starTime').read().rstrip('\n')       
      countTry += 1 
      time.sleep(15)       
   #}

   txFile.write(jobKey + "_" + index + "| Tx: " + txHash + "| setJobStatus_started" +  " " + starTime + "\n") 
   txFile.close() 
#}

if __name__ == '__main__': #{
   jobKey   = sys.argv[1] 
   index    = sys.argv[2] 
   jobID    = sys.argv[3] 
   
   startCall(jobKey, index, jobID) 
#}
