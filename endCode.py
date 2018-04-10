#!/usr/bin/env python

from subprocess import call
import sys, os, time, subprocess, constants, base64

jobKeyGlobal    = "";
indexGlobal     = "";

def logTest(strIn): #{
   print(strIn);
   txFile = open(constants.LOG_PATH + '/endCodeAnalyse/' + jobKeyGlobal + "_" + indexGlobal + '.txt', 'a');
   txFile.write(strIn + "\n"); 
   txFile.close();
#}

def receiptCheckTx(): #{
   transactionHash = os.popen('node $eblocPath/eBlocBrokerNodeCall.js receiptCheck $jobKey $index $elapsedRawTime $newHash $storageType $endTimeStamp').read().rstrip('\n').replace(" ", ""); 

   while(True): #{
      if not(transactionHash == "notconnected" or transactionHash == ""): 
         break;
      else:
         logTest("Error: Please run Parity or Geth on the background.")
         transactionHash = os.popen('node $eblocPath/eBlocBrokerNodeCall.js receiptCheck $jobKey $index $elapsedRawTime $newHash $storageType $endTimeStamp').read().rstrip('\n').replace(" ", ""); 
      time.sleep(5);
   #}
   
   logTest("ReceiptHash: " + transactionHash); 
   txFile = open(constants.LOG_PATH + '/transactions/' + constants.CLUSTER_ID + '.txt', 'a');   
   txFile.write(transactionHash + " receiptCheckTx\n");
   txFile.close();
#}

def endCall(jobKey, index, storageType, shareToken, miniLockId, folderName): #{
   endTimeStamp = os.popen('date +%s').read(); 

   global jobKeyGlobal; jobKeyGlobal = jobKey
   global indexGlobal;  indexGlobal  = index;

   os.environ['endTimeStamp'] = endTimeStamp;
   logTest("endTimeStamp: " + endTimeStamp)

   # Paths--------------------------------------
   contractCallPath = constants.EBLOCPATH + '/contractCalls'; os.environ['contractCallPath'] = contractCallPath;
   programPath      = constants.PROGRAM_PATH;
   # -------------------------------------------   
   encodedShareToken = '';
   if shareToken != '-1':
      encodedShareToken = base64.b64encode(shareToken + ':')

   header = "var eBlocBroker = require('" + constants.EBLOCPATH + "/eBlocBrokerHeader.js')"; os.environ['header'] = header;

   os.environ['programPath']       = str(programPath);
   os.environ['clusterID']         = constants.CLUSTER_ID;
   os.environ['GDRIVE_METADATA']   = constants.GDRIVE_METADATA;
   os.environ['jobKey']            = jobKey;
   os.environ['index']             = str(index);
   os.environ["IPFS_PATH"]         = constants.IPFS_REPO; # Default IPFS repo path
   os.environ['eblocPath']         = constants.EBLOCPATH;
   os.environ['encodedShareToken'] = encodedShareToken;
   os.environ['clientMiniLockId']  = miniLockId;
   os.environ['jobName']           = folderName;
   os.environ['storageType']       = str(storageType);

   logTest(jobKey + ' ' + index + ' ' + storageType + ' ' + shareToken + ' ' + miniLockId + ' ' + folderName);
   
   if os.path.isfile(programPath + '/' + jobKey + "_" + index + '/modifiedDate.txt'):
      fDate = open(programPath + '/' + jobKey + "_" + index + '/modifiedDate.txt', 'r')
      modifiedDate = fDate.read().rstrip('\n');
      os.environ['modifiedDate'] = modifiedDate;
      fDate.close();
      logTest(modifiedDate);
      
   logTest("jobKey: "            + jobKey);
   logTest("index: "             + index);
   logTest("storageType: "       + storageType);
   logTest("shareToken: "        + shareToken);
   logTest("encodedShareToken: " + encodedShareToken);
   logTest("miniLockId: "        + miniLockId);
   logTest("folderName: "        + folderName);

   logTest("whoami: " + os.popen('whoami').read().rstrip('\n'));
   logTest("pwd: "    + os.popen('pwd').read().rstrip('\n'));
   
   resultsFolder = programPath + "/" + jobKey + "_" + index; 
   os.environ['resultsFolder'] = resultsFolder;
   logTest("resultsFolder: " + resultsFolder);

   jobInfo = os.popen('$contractCallPath/getJobInfo.py $clusterID $jobKey $index 2>/dev/null').read().rstrip('\n').replace(" ","")[1:-1];
   logTest(os.popen('echo $contractCallPath/getJobInfo.py $clusterID $jobKey $index').read().rstrip('\n'));
   while(True):
      if not(jobInfo == "Connection refused" or jobInfo == "" or jobInfo == "Errno"): 
         break;
      else:
         logTest('jobInfo: ' + jobInfo);
         logTest(os.popen('echo $contractCallPath/getJobInfo.py $clusterID $jobKey $index').read().rstrip('\n'));
         logTest("Error: Please run Parity or Geth on the background.")
         jobInfo = os.popen('$contractCallPath/getJobInfo.py $clusterID $jobKey $index 2>/dev/null').read().rstrip('\n').replace(" ","")[1:-1];         
      time.sleep(1)

   logTest("JOB_INFO:" + jobInfo)
   jobInfo = jobInfo.split(',');

   if jobInfo[0] == str(constants.job_state_code['COMPLETED']): #{
      logTest('Job is already get paid.')
      sys.exit();
   #}

   clientTimeLimit = jobInfo[5];
   logTest("clientGasMinuteLimit: " + clientTimeLimit); # Clients minuteGas for the job
      
   countTry = 0;
   while True: #{
      if countTry > 10:
         sys.exit()
      countTry = countTry + 1                  

      logTest("Waiting... "); 

      if jobInfo[0] == str(constants.job_state_code['RUNNING']): # It will come here eventually, when setJob() is deployed.
         logTest("Job started running"); 
         break; # Wait until does values updated on the blockchain
      
      if jobInfo[0] == constants.job_state_code['COMPLETED']: 
        logTest( "Error: Already completed job..."); 
        sys.exit(); # Detects an error on the SLURM side

      jobInfo = os.popen('$contractCallPath/getJobInfo.py $clusterID $jobKey $index 2>/dev/null').read().rstrip('\n').replace(" ","")[1:-1];         
      while(True):
         if(not(jobInfo == "Connection refused" or jobInfo == "" or jobInfo == "Errno")): 
            break;
         else:
            logTest("Error: Please run Parity or Geth on the background.****************************")
            jobInfo = os.popen('$contractCallPath/getJobInfo.py $clusterID $jobKey $index 2>/dev/null').read().rstrip('\n').replace(" ","")[1:-1];         
         time.sleep(1)
      jobInfo = jobInfo.split(',');
      time.sleep(30) # Short sleep here so this loop is not keeping CPU busy
   #}
   
   logTest("jobName: " + str(folderName));
   jobId = os.popen("sacct --name $jobName.sh  -n | awk '{print $1}' | head -n 1 | sed -r 's/[.batch]+//g' ").read().rstrip('\n'); os.environ['jobId'] = jobId;
   logTest("JOBID ------------> " + str(jobId));

   # Here we know that job is already completed ----------------
   ''' uncomment!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!1
   if str(storageType) == '0' or str(storageType) == '3': #{
      countTry = 0;
      while(True): 
         if (countTry > 10):
            sys.exit()
         countTry = countTry + 1         

         #os.chdir(resultsFolder);
         #os.popen('find . -type f ! -newer $resultsFolder/modifiedDate.txt -delete');
         newHash = os.popen('ipfs add -r ' + programPath + '/${jobKey}_$index').read();  

         if (newHash == ""):
            logTest("Generated new hash return empty error. Trying again...");
         else:
            os.environ['newHash'] = newHash;
            newHash = os.popen('echo $newHash | tr " " "\n" | tail -n2 | head -n1' ).read().rstrip('\n'); 
            os.environ['newHash'] = newHash;
            logTest("newHash: " + newHash); 
            break
   #}
   '''
   if str(storageType) == '2': #{      
      os.chdir(resultsFolder);
      res = os.popen('tar -P -cvzf $resultsFolder/result.tar.gz .').read();
      logTest("tarRes: " + res)

      res = os.popen('mlck encrypt -f $resultsFolder/result.tar.gz $clientMiniLockId --anonymous --output-file=$resultsFolder/result.tar.gz.minilock').read();
      logTest(res);           
      os.system('find $resultsFolder -type f ! -newer $resultsFolder/modifiedDate.txt -delete');

      countTry = 0;
      while(True): 
         if countTry > 10:
            sys.exit()
         countTry = countTry + 1;
         
         newHash = os.popen('ipfs add $resultsFolder/result.tar.gz.minilock').read();
         logTest("newHash: " + newHash) 
         newHash = newHash.split(" ")[1];

         if (newHash == ""):
            logTest("Generated new hash return empty error. Trying again.");
         else:
            os.environ['newHash'] = newHash;
            newHash = os.popen('echo $newHash | tr " " "\n" | tail -n2 | head -n1' ).read().rstrip('\n'); os.environ['newHash'] = newHash;
            logTest("newHash: " + newHash);
            break;
   #}
      
   logTest("jobId: " + jobId);
   elapsedTime = os.popen('sacct -j $jobId --format="Elapsed" | tail -n1 | head -n1').read();
   logTest("ElapsedTime: " + elapsedTime);

   elapsedTime    = elapsedTime.split(':');
   elapsedDay     = "0";
   elapsedHour    = elapsedTime[0].replace(" ", "");
   elapsedMinute  = elapsedTime[1].rstrip();
   elapsedSeconds = elapsedTime[2].rstrip();

   if "-" in str(elapsedHour):
      # logTest(elapsedHour)
      elapsedHour = elapsedHour.split('-');
      elapsedDay  = elapsedHour[0];
      elapsedHour = elapsedHour[1];

   elapsedRawTime = int(elapsedDay)* 1440 + int(elapsedHour) * 60 + int(elapsedMinute) + 1;
   logTest("ElapsedRawTime: " + str(elapsedRawTime))

   if elapsedRawTime > int(clientTimeLimit):
      elapsedRawTime = clientTimeLimit

   os.environ['elapsedRawTime'] = str(elapsedRawTime);
   logTest("finalizedElapsedRawTime: " + str(elapsedRawTime));
   logTest("jobInfo: " + str(jobInfo));

   if storageType == '1': #{
      os.environ['newHash'] = "0x00";
   
      jobKeyTemp = jobKey.split('=');
      folderName = jobKeyTemp[1];
      logTest(folderName);
      
      os.system("rm $resultsFolder/.node-xmlhttprequest*");
      
      os.chdir(resultsFolder) 
      os.popen('find . -type f ! -newer $resultsFolder/modifiedDate.txt -delete') # Client's loaded files are deleted, no need to re-upload them
      os.popen('zip -r results_$index.zip .') 
      res = os.popen('curl -X PUT -H \'Content-Type: text/plain\' -H \'Authorization: Basic \'$encodedShareToken\'==\' --data-binary \'@results_\'$index\'.zip\' https://b2drop.eudat.eu/public.php/webdav/results_$index.zip').read();
      #os.system("rm -rf " + programPath + '/' + jobKey + "_" + index); # Deleted downloaded code from local since it is not needed anymore
   #}   
   elif str(storageType) == '3': #{ == '4'
      os.environ['newHash'] = "0x00";            
      mimeType = os.popen('gdrive info $jobKey -c $GDRIVE_METADATA | grep \'Mime\' | awk \'{print $2}\'').read().rstrip('\n');
      logTest('mimeType: ' + mimeType); #delete
      
      if 'folder' in mimeType:
         logTest('folder');         
         os.chdir(resultsFolder);         
         os.system('find . -type f ! -newer $resultsFolder/modifiedDate.txt -delete'); # Client's loaded files are deleted, no need to re-upload them
         res = os.popen('zip -r results_$index.zip .').read();
         logTest(res);
         time.sleep(0.25);         
         res = os.popen('gdrive upload --parent $jobKey results_$index.zip -c $GDRIVE_METADATA').read();
         logTest(res);

      elif 'gzip' in mimeType:
         print('zip');      

   #}
   
   receiptCheckTx();   
#}

if __name__ == '__main__': #{
   jobKey      = sys.argv[1];
   index       = sys.argv[2];
   storageType = sys.argv[3];
   shareToken  = sys.argv[4];
   miniLockId  = sys.argv[5];
   folderName  = sys.argv[6];

   endCall(jobKey, index, storageType, shareToken, miniLockId, folderName)
#}
