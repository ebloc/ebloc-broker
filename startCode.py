#!/usr/bin/env python

import sys, os, constants, time

def startCall( jobKey, index ):
   cluster_id = constants.CLUSTER_ID;
   eblocPath  = constants.EBLOCPATH; 
   logPath    = constants.LOG_PATH; 

   os.environ['eblocPath'] = eblocPath;
   os.environ['index']     = str(index);
   os.environ['jobKey']    = jobKey;
   statusId                = str(constants.job_state_code['RUNNING']); 
   os.environ['statusId']  = statusId;
   
   unixTime                = os.popen('date +%s').read();
   unixTime                = str(int(unixTime) + 1)
   os.environ['unixTime']  = unixTime
   txHash = os.popen('node $eblocPath/eBlocBrokerNodeCall.js setJobStatus $jobKey $index $statusId $unixTime').read().replace("\n", "").replace(" ", "");
   
   while(True):
      if (not(txHash == "notconnected" or txHash == "")): 
         break;
      else:
         os.environ['unixTime'] = unixTime;
         txHash = os.popen('node $eblocPath/eBlocBrokerNodeCall.js setJobStatus $jobKey $index $statusId $unixTime').read().replace("\n", "").replace(" ", "");        
      time.sleep(5)
      
   txFile = open( logPath + '/transactions/' + cluster_id + '.txt', 'a');
   txFile.write( txHash + " start_setJobStatus" +  " " + unixTime + "\n");
   txFile.close();
   
if __name__ == '__main__': 
   jobKey   = sys.argv[1];
   index    = sys.argv[2];
   startCall( jobKey, index );
