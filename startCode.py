#!/usr/bin/env python

import sys, lib, time, subprocess

def startCall(jobKey, index, jobID): #{
   statusID                = str(lib.job_state_code['RUNNING'])

   # cmd: scontrol show job jobID | grep 'StartTime'| grep -o -P '(?<=StartTime=).*(?= E)'
   p1 = subprocess.Popen(['scontrol', 'show', 'job', jobID], stdout=subprocess.PIPE)
   #-----------
   p2 = subprocess.Popen(['grep', 'StartTime'], stdin=p1.stdout, stdout=subprocess.PIPE)
   p1.stdout.close()
   #-----------
   p3 = subprocess.Popen(['grep', '-o', '-P', '(?<=StartTime=).*(?= E)'], stdin=p2.stdout,stdout=subprocess.PIPE)
   p2.stdout.close()
   date      = p3.communicate()[0].decode('utf-8').strip()
   # cmd: date -d 2018-09-09T18:38:29 +"%s"
   startTime = subprocess.check_output(["date", "-d", date, '+\'%s\'']).strip().decode('utf-8').replace("\'","")
   
   txFile = open(lib.LOG_PATH + '/transactions/' + lib.CLUSTER_ID + '.txt', 'a')        
   txFile.write(lib.EBLOCPATH + "/contractCalls/setJobStatus.py" + ' ' + jobKey + ' ' + index + ' ' + statusID + ' ' + startTime + '\n')    
   time.sleep(0.25) 

   countTry = 0    
   txHash = subprocess.check_output(["python", lib.EBLOCPATH + "/contractCalls/setJobStatus.py",
                                     jobKey, index, statusID, startTime]).decode('utf-8').strip()
   while txHash == "notconnected" or txHash == "": #{
      if countTry > 10:
         sys.exit() 
      txFile.write(jobKey + "_" + index + "| Try: " + str(countTry) + " " + txHash + '\n') 
      txHash = subprocess.check_output(["python", lib.EBLOCPATH + "/contractCalls/setJobStatus.py",
                                        jobKey, index, statusID, startTime]).decode('utf-8').strip()      
      countTry += 1 
      time.sleep(15)       
   #}

   txFile.write(jobKey + "_" + index + "| Tx: " + txHash + "| setJobStatus_started" +  " " + startTime + "\n") 
   txFile.close() 
#}

if __name__ == '__main__': #{
   jobKey   = sys.argv[1] 
   index    = sys.argv[2] 
   jobID    = sys.argv[3] 
   
   startCall(jobKey, index, jobID) 
#}
