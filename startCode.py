#!/usr/bin/env python

import sys, os, constants, time

contractCallPath               = constants.EBLOCPATH + '/contractCalls';
os.environ['contractCallPath'] = contractCallPath;

def startCall(jobKey, index): #{
   os.environ['eblocPath'] = constants.EBLOCPATH;
   os.environ['index']     = str(index);
   os.environ['jobKey']    = jobKey;
   statusId                = str(constants.job_state_code['RUNNING']);
   os.environ['statusId']  = statusId;   
   unixTime                = str(int(os.popen('date +%s').read()) + 1);
   os.environ['unixTime']  = unixTime;

   '''
   resultsFolderPrev = constants.PROGRAM_PATH + "/" + jobKey + "_" + index;
   txFile = open(resultsFolderPrev + '/unixTime.txt', 'w');
   txFile.write(unixTime);   
   txFile.close();
   time.sleep(0.25);
   '''
   resultsFolderPrev = constants.PROGRAM_PATH + "/" + jobKey + "_" + index;
   txFile = open(resultsFolderPrev + '/unixTime.txt', 'w');
   txFile.write(os.popen('echo $contractCallPath/setJobStatus.py $jobKey $index $statusId $unixTime').read().rstrip('\n'));   
   txFile.close();
   time.sleep(0.25);   

   # txHash = os.popen('$contractCallPath/setJobStatus.py $jobKey $index $statusId $unixTime').read().rstrip('\n');
   txHash = os.popen('node $eblocPath/eBlocBrokerNodeCall.js setJobStatus $jobKey $index $statusId $unixTime').read().rstrip('\n').replace(" ", "");
   txFile = open(constants.LOG_PATH + '/transactions/' + constants.CLUSTER_ID + '.txt', 'a');

   countTry = 0;
   while True: #{
      if countTry > 10:
         sys.exit()
      countTry = countTry + 1                  
      
      if not(txHash == "notconnected" or txHash == ""): 
         break;      
      else:
         os.environ['unixTime'] = unixTime;
         # txHash = os.popen('$contractCallPath/setJobStatus.py $jobKey $index $statusId $unixTime').read().rstrip('\n');
         txHash = os.popen('node $eblocPath/eBlocBrokerNodeCall.js setJobStatus $jobKey $index $statusId $unixTime').read().rstrip('\n').replace(" ", "");         
      txFile.write(jobKey + "_" + index + "| Try: " + str(countTry) + '\n');
      time.sleep(5);      
   #}

   txFile.write(jobKey + "_" + index + "| Tx: " + txHash + "| setJobStatus_started" +  " " + unixTime + "\n");
   txFile.close();
#}

if __name__ == '__main__': #{
   jobKey   = sys.argv[1];
   index    = sys.argv[2];
   startCall(jobKey, index);
#}
