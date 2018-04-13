#!/usr/bin/env python

from subprocess import call
import sys, os, time, subprocess, constants, base64

jobKeyGlobal    = "";
indexGlobal     = "";

def log(strIn): #{
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
         log("Error: Please run Parity or Geth on the background.")
         transactionHash = os.popen('node $eblocPath/eBlocBrokerNodeCall.js receiptCheck $jobKey $index $elapsedRawTime $newHash $storageType $endTimeStamp').read().rstrip('\n').replace(" ", ""); 
      time.sleep(5);
   #}
   
   log("ReceiptHash: " + transactionHash); 
   txFile = open(constants.LOG_PATH + '/transactions/' + constants.CLUSTER_ID + '.txt', 'a');   
   txFile.write(transactionHash + " receiptCheckTx\n");
   txFile.close();
#}

def endCall(jobKey, index, storageType, shareToken, miniLockId, folderName): #{
   endTimeStamp = os.popen('date +%s').read(); 
   global jobKeyGlobal; jobKeyGlobal = jobKey
   global indexGlobal;  indexGlobal  = index;

   os.environ['endTimeStamp'] = endTimeStamp;
   log("endTimeStamp: " + endTimeStamp);

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

   log(jobKey + ' ' + index + ' ' + storageType + ' ' + shareToken + ' ' + miniLockId + ' ' + folderName);

   resultsFolder = programPath + "/" + jobKey + "_" + index + '/JOB_TO_RUN'; 
   os.environ['resultsFolder'] = resultsFolder;
   log("resultsFolder: " + resultsFolder);

   if os.path.isfile(resultsFolder + '/modifiedDate.txt'):
      fDate = open(resultsFolder + '/modifiedDate.txt', 'r')
      modifiedDate = fDate.read().rstrip('\n');
      os.environ['modifiedDate'] = modifiedDate;
      fDate.close();
      log(modifiedDate);
      
   log("whoami: "            + os.popen('whoami').read().rstrip('\n'));
   log("pwd: "               + os.popen('pwd').read().rstrip('\n'));
   log("jobKey: "            + jobKey);
   log("index: "             + index);
   log("storageType: "       + storageType);
   log("shareToken: "        + shareToken);
   log("encodedShareToken: " + encodedShareToken);
   log("miniLockId: "        + miniLockId);
   log("folderName: "        + folderName);
   log("clusterID: "         + constants.CLUSTER_ID);

   jobInfo = os.popen('$contractCallPath/getJobInfo.py $clusterID $jobKey $index 2>/dev/null').read().rstrip('\n').replace(" ","")[1:-1];

   while True:
      if not(jobInfo == "Connection refused" or jobInfo == "" or jobInfo == "Errno"): 
         break;
      else:
         log('jobInfo: ' + jobInfo);
         log(os.popen('echo $contractCallPath/getJobInfo.py $clusterID $jobKey $index').read().rstrip('\n'));
         log("Error: Please run Parity or Geth on the background.")
         jobInfo = os.popen('$contractCallPath/getJobInfo.py $clusterID $jobKey $index 2>/dev/null').read().rstrip('\n').replace(" ","")[1:-1];         
      time.sleep(1)

   log("JOB_INFO:" + jobInfo)
   jobInfo = jobInfo.split(',');

   if jobInfo[0] == str(constants.job_state_code['COMPLETED']): #{
      log('Job is already get paid.')
      sys.exit();
   #}

   clientTimeLimit = jobInfo[5];
   log("clientGasMinuteLimit: " + clientTimeLimit); # Clients minuteGas for the job
      
   countTry = 0;
   while True: #{
      log("Waiting... " + str(countTry)); 
      if countTry > 25:
         sys.exit()
      countTry = countTry + 1                  

      if jobInfo[0] == str(constants.job_state_code['RUNNING']): # It will come here eventually, when setJob() is deployed.
         log("Job started running"); 
         break; # Wait until does values updated on the blockchain
      
      if jobInfo[0] == constants.job_state_code['COMPLETED']: 
        log( "Error: Already completed job..."); 
        sys.exit(); # Detects an error on the SLURM side

      jobInfo = os.popen('$contractCallPath/getJobInfo.py $clusterID $jobKey $index 2>/dev/null').read().rstrip('\n').replace(" ","")[1:-1];         
      while True:
         if(not(jobInfo == "Connection refused" or jobInfo == "" or jobInfo == "Errno")): 
            break;
         else:
            log("Error: Please run Parity or Geth on the background.****************************")
            jobInfo = os.popen('$contractCallPath/getJobInfo.py $clusterID $jobKey $index 2>/dev/null').read().rstrip('\n').replace(" ","")[1:-1];         
         time.sleep(1)
      jobInfo = jobInfo.split(',');
      time.sleep(30) # Short sleep here so this loop is not keeping CPU busy
   #}
   
   log("jobName: " + str(folderName));
   jobId = os.popen("sacct --name $jobName.sh  -n | awk '{print $1}' | head -n 1 | sed -r 's/[.batch]+//g' ").read().rstrip('\n'); os.environ['jobId'] = jobId;
   log("JOBID ------------> " + str(jobId));

   # Here we know that job is already completed ----------------
   if str(storageType) == '0' or str(storageType) == '3': #{
      countTry = 0;
      while True: 
         if (countTry > 10):
            sys.exit()
         countTry = countTry + 1         

         #os.chdir(resultsFolder);
         #os.popen('find . -type f ! -newer $resultsFolder/modifiedDate.txt -delete');
         newHash = os.popen('ipfs add -r ' + programPath + '/${jobKey}_$index').read();  

         if (newHash == ""):
            log("Generated new hash return empty error. Trying again...");
         else:
            os.environ['newHash'] = newHash;
            newHash = os.popen('echo $newHash | tr " " "\n" | tail -n2 | head -n1' ).read().rstrip('\n'); 
            os.environ['newHash'] = newHash;
            log("newHash: " + newHash); 
            break
   #}

   if str(storageType) == '2': #{      
      os.chdir(resultsFolder);
      res = os.popen('tar -P -cvzf $resultsFolder/result.tar.gz .').read();
      log("tarRes: " + res)

      res = os.popen('mlck encrypt -f $resultsFolder/result.tar.gz $clientMiniLockId --anonymous --output-file=$resultsFolder/result.tar.gz.minilock').read();
      log(res);           
      os.system('find $resultsFolder -type f ! -newer $resultsFolder/modifiedDate.txt -delete');

      countTry = 0;
      while True: 
         if countTry > 10:
            sys.exit()
         countTry = countTry + 1;
         
         newHash = os.popen('ipfs add $resultsFolder/result.tar.gz.minilock').read();
         log("newHash: " + newHash) 
         newHash = newHash.split(" ")[1];

         if (newHash == ""):
            log("Generated new hash return empty error. Trying again.");
         else:
            os.environ['newHash'] = newHash;
            newHash = os.popen('echo $newHash | tr " " "\n" | tail -n2 | head -n1' ).read().rstrip('\n'); os.environ['newHash'] = newHash;
            log("newHash: " + newHash);
            break;
   #}
      
   log("jobId: " + jobId);
   elapsedTime = os.popen('sacct -j $jobId --format="Elapsed" | tail -n1 | head -n1').read();
   log("ElapsedTime: " + elapsedTime);

   elapsedTime    = elapsedTime.split(':');
   elapsedDay     = "0";
   elapsedHour    = elapsedTime[0].replace(" ", "");
   elapsedMinute  = elapsedTime[1].rstrip();
   elapsedSeconds = elapsedTime[2].rstrip();

   if "-" in str(elapsedHour):
      # log(elapsedHour)
      elapsedHour = elapsedHour.split('-');
      elapsedDay  = elapsedHour[0];
      elapsedHour = elapsedHour[1];

   elapsedRawTime = int(elapsedDay)* 1440 + int(elapsedHour) * 60 + int(elapsedMinute) + 1;
   log("ElapsedRawTime: " + str(elapsedRawTime))

   if elapsedRawTime > int(clientTimeLimit):
      elapsedRawTime = clientTimeLimit;

   os.environ['elapsedRawTime'] = str(elapsedRawTime);
   log("finalizedElapsedRawTime: " + str(elapsedRawTime));
   log("jobInfo: " + str(jobInfo));

   if storageType == '1': #{
      os.environ['newHash'] = "0x00";
   
      jobKeyTemp = jobKey.split('=');
      folderName = jobKeyTemp[1];
      log(folderName);
      
      os.system("rm $resultsFolder/.node-xmlhttprequest*");      
      os.chdir(resultsFolder);

      os.environ['c'] = constants.CLUSTER_ID[2:]; #0x is removed
      os.popen('find . -type f ! -newer $resultsFolder/modifiedDate.txt -delete'); # Client's loaded files are deleted, no need to re-upload them.
      log(os.popen('zip -r result-$c-$index.zip .').read());
      
      os.system('curl -X PUT -H \'Content-Type: text/plain\' -H \'Authorization: Basic \'$encodedShareToken\'==\' --data-binary \'@result-\'$c\'-\'$index\'.zip\' https://b2drop.eudat.eu/public.php/webdav/result-$c-$index.zip');
      #os.system("rm -rf " + programPath + '/' + jobKey + "_" + index); # Deleted downloaded code from local since it is not needed anymore
   #}   
   elif str(storageType) == '4': #{ 
      os.environ['newHash'] = "0x00";            
      mimeType = os.popen('gdrive info $jobKey -c $GDRIVE_METADATA | grep \'Mime\' | awk \'{print $2}\'').read().rstrip('\n');
      
      if 'folder' in mimeType:
         log('folder');         
         os.chdir(resultsFolder);         
         os.system('find . -type f ! -newer $resultsFolder/modifiedDate.txt -delete'); # Client's loaded files are deleted, no need to re-upload them
         res = os.popen('zip -r result-$c-$index.zip .').read();
         log(res);
         time.sleep(0.25);         
         res = os.popen('gdrive upload --parent $jobKey result-$c-$index.zip -c $GDRIVE_METADATA').read();
         log(res);

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
