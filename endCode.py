#!/usr/bin/env python

from subprocess import call
import sys, os, time, subprocess, constants, base64
from colored import stylize
from colored import fg

jobKeyGlobal    = "";
indexGlobal     = "";

def log(strIn, color=''): #{
   if color != '':
      print(stylize(strIn, fg(color)));
   else:
      print(strIn)

   txFile = open(constants.LOG_PATH + '/endCodeAnalyse/' + jobKeyGlobal + "_" + indexGlobal + '.txt', 'a');
   txFile.write(strIn + "\n"); 
   txFile.close();
#}

def receiptCheckTx(): #{
   transactionHash = os.popen('node $eblocPath/eBlocBrokerNodeCall.js receiptCheck $jobKey $index $elapsedRawTime $newHash $storageID $endTimeStamp').read().rstrip('\n').replace(" ", ""); 

   while(True): #{
      if not(transactionHash == "notconnected" or transactionHash == ""): 
         break;
      else:
         log("Error: Please run Parity or Geth on the background.", 'red')
         transactionHash = os.popen('node $eblocPath/eBlocBrokerNodeCall.js receiptCheck $jobKey $index $elapsedRawTime $newHash $storageID $endTimeStamp').read().rstrip('\n').replace(" ", ""); 
      time.sleep(5);
   #}
   
   log("ReceiptHash: " + transactionHash); 
   txFile = open(constants.LOG_PATH + '/transactions/' + constants.CLUSTER_ID + '.txt', 'a');   
   txFile.write(transactionHash + " receiptCheckTx\n");
   txFile.close();
#}

def endCall(jobKey, index, storageID, shareToken, folderName): #{
   endTimeStamp = os.popen('date +%s').read(); 
   global jobKeyGlobal; jobKeyGlobal = jobKey
   global indexGlobal;  indexGlobal  = index;

   os.environ['endTimeStamp'] = endTimeStamp;
   log("endTimeStamp: " + endTimeStamp);

   # Paths--------------------------------------
   contractCallPath      = constants.EBLOCPATH + '/contractCalls'; 
   programPath           = constants.PROGRAM_PATH;   
   os.environ['contractCallPath'] = contractCallPath;
   os.environ['logPath'] = constants.LOG_PATH;
   # -------------------------------------------   

   encodedShareToken = '';
   if shareToken != '-1':
      encodedShareToken = base64.b64encode(shareToken + ':')
      
   os.environ['programPath']       = str(programPath);
   os.environ['clusterID']         = constants.CLUSTER_ID;
   os.environ['GDRIVE_METADATA']   = constants.GDRIVE_METADATA;
   os.environ['jobKey']            = jobKey;
   os.environ['index']             = str(index);
   os.environ["IPFS_PATH"]         = constants.IPFS_REPO; # Default IPFS repo path
   os.environ['eblocPath']         = constants.EBLOCPATH;
   os.environ['encodedShareToken'] = encodedShareToken;  
   os.environ['jobName']           = folderName;
   os.environ['storageID']       = str(storageID);

   log(jobKey + ' ' + index + ' ' + storageID + ' ' + shareToken + ' ' + folderName);

   resultsFolder     = programPath + "/" + jobKey + "_" + index + '/JOB_TO_RUN';
   resultsFolderPrev = programPath + "/" + jobKey + "_" + index;
   os.environ['resultsFolder']     = resultsFolder;
   os.environ['resultsFolderPrev'] = resultsFolderPrev;

   if os.path.isfile(resultsFolderPrev + '/modifiedDate.txt'): #{
      fDate = open(resultsFolderPrev + '/modifiedDate.txt', 'r')
      modifiedDate = fDate.read().rstrip('\n');
      os.environ['modifiedDate'] = modifiedDate;
      fDate.close();
      log(modifiedDate);
   #}
   
   jobInfo = os.popen('$contractCallPath/getJobInfo.py $clusterID $jobKey $index 2>/dev/null').read().rstrip('\n').replace(" ","")[1:-1];

   while True: #{
      if not(jobInfo == "Connection refused" or jobInfo == "" or jobInfo == "Errno"): 
         break;
      else:
         log('jobInfo: ' + jobInfo);
         log(os.popen('echo $contractCallPath/getJobInfo.py $clusterID $jobKey $index').read().rstrip('\n'));
         log("Error: Please run Parity or Geth on the background.", 'red')
         jobInfo = os.popen('$contractCallPath/getJobInfo.py $clusterID $jobKey $index 2>/dev/null').read().rstrip('\n').replace(" ","")[1:-1];         
      time.sleep(1)
   #}


   log("JOB_INFO:" + jobInfo)
   jobInfo = jobInfo.split(',');

   os.environ['userID'] = jobInfo[6].replace("u'", "").replace("'", "");
   # userInfo = os.popen('#!/bin/bash; source venv/bin/activate; python3 $contractCallPath/getUserInfo.py $userID 1  2>/dev/null').read().rstrip('\n').replace(" ", "");

   userInfo = os.popen('. $eblocPath/venv/bin/activate && $eblocPath/venv/bin/python3 $contractCallPath/getUserInfo.py $userID 1').read().rstrip('\n').replace(" ", "");
   # log(userInfo)    # delete
   # log(os.popen('echo python3 $contractCallPath/getUserInfo.py $userID 1').read()) #delete
   # log(os.popen('which python3').read()) #delete
   
   # constants.contractCall('eBlocBroker.getUserInfo(\'$resultsFolderPrev/userInfo.txt\', \'$userID\')'); #|
   # time.sleep(1);                                                                                       #|
   # userInfo = os.popen('cat $resultsFolderPrev/userInfo.txt').read().replace(" ", "");                  #|

   log("\nwhoami: "          + os.popen('whoami').read().rstrip('\n'));
   log("pwd: "               + os.popen('pwd').read().rstrip('\n'));
   log("resultsFolder: "     + resultsFolder);
   log("jobKey: "            + jobKey);
   log("index: "             + index);
   log("storageID: "         + storageID);
   log("shareToken: "        + shareToken);
   log("encodedShareToken: " + encodedShareToken);   
   log("folderName: "        + folderName);
   log("clusterID: "         + constants.CLUSTER_ID);

   if ',' in userInfo: #{
      userInfo = userInfo.split(',');
      log("jobOwner's Info: "); 
      log('{0: <13}'.format('userEmail: ')     + userInfo[1])
      log('{0: <13}'.format('miniLockID: ')    + userInfo[2])
      log('{0: <13}'.format('ipfsAddress: ')   + userInfo[3])
      log('{0: <13}'.format('fID: ')           + userInfo[4])
      os.environ['clientMiniLockId']  = userInfo[2];
   #}
   else:     
      log("userInfo split Failure")
      
   log("");
   
   if jobInfo[0] == str(constants.job_state_code['COMPLETED']): #{
      log('Job is already get paid.', 'red');
      sys.exit();
   #}

   clientTimeLimit = jobInfo[5];
   log("clientGasMinuteLimit: " + clientTimeLimit); # Clients minuteGas for the job
      
   countTry = 0;
   while True: #{
      log("Waiting... " + str(countTry), 'yellow'); 
      if countTry > 25:
         sys.exit()
      countTry = countTry + 1                  

      if jobInfo[0] == str(constants.job_state_code['RUNNING']): # It will come here eventually, when setJob() is deployed.
         log("Job started to run.", 'green'); 
         break; # Wait until does values updated on the blockchain
      
      if jobInfo[0] == constants.job_state_code['COMPLETED']: 
        log( "Error: Already completed job is received.", 'red'); 
        sys.exit(); # Detects an error on the SLURM side

      jobInfo = os.popen('$contractCallPath/getJobInfo.py $clusterID $jobKey $index 2>/dev/null').read().rstrip('\n').replace(" ","")[1:-1];         
      while True:
         if(not(jobInfo == "Connection refused" or jobInfo == "" or jobInfo == "Errno")): 
            break;
         else:
            log("Error: Please run Parity or Geth on the background.", 'red')
            jobInfo = os.popen('$contractCallPath/getJobInfo.py $clusterID $jobKey $index 2>/dev/null').read().rstrip('\n').replace(" ","")[1:-1];         
         time.sleep(1)
      jobInfo = jobInfo.split(',');
      time.sleep(30) # Short sleep here so this loop is not keeping CPU busy
   #}
   
   log("jobName: " + str(folderName));
   jobId = os.popen("sacct --name $jobName.sh  -n | awk '{print $1}' | head -n 1 | sed -r 's/[.batch]+//g' ").read().rstrip('\n'); os.environ['jobId'] = jobId;
   log("JOBID ==> " + str(jobId));

   # Here we know that job is already completed 
   if str(storageID) == '0' or str(storageID) == '3': #{
      countTry = 0;
      while True: 
         if (countTry > 10):
            sys.exit()
         countTry = countTry + 1         

         os.chdir(resultsFolder);         
         # os.popen('find . -type f ! -newer $resultsFolderPrev/modifiedDate.txt -delete'); # Not needed, already uploaded files won't uploaded again.
         
         # log(os.popen('d=$(cat $resultsFolderPrev/modifiedDate.txt); tar -N \'$d\' -jcvf result.tar.gz *').read()); #| 
         # newHash = os.popen('ipfs add ' + resultsFolder + '/result.tar.gz').read();                                 #| Upload as .tar.gz.
         # log(os.popen('rm -f $resultsFolder/result.tar.gz').read()); #un-comment                                    #|
         
         newHash = os.popen('ipfs add -r $resultsFolder').read(); # Upload as folder.                                    
         if newHash == "":
            log("Generated new hash return empty error. Trying again...", 'yellow');
         else: #{
            os.environ['newHash'] = newHash;
            newHash = os.popen('echo $newHash | tr " " "\n" | tail -n2 | head -n1' ).read().rstrip('\n'); 
            os.environ['newHash'] = newHash;
            log("newHash: " + newHash); 
            break
         #}
   #}

   if str(storageID) == '2': #{      
      os.chdir(resultsFolder);
      log(os.popen('d=$(cat $resultsFolderPrev/modifiedDate.txt); tar -N \'$d\' -jcvf result.tar.gz *').read());
      #log(os.popen('tar -P -cvzf $resultsFolder/result.tar.gz .').read());      

      log(os.popen('mlck encrypt -f $resultsFolder/result.tar.gz $clientMiniLockId --anonymous --output-file=$resultsFolder/result.tar.gz.minilock').read());
      # os.system('find $resultsFolder -type f ! -newer $resultsFolder/modifiedDate.txt -delete');

      countTry = 0;
      while True: 
         if countTry > 10:
            sys.exit()
         countTry = countTry + 1;
         
         newHash = os.popen('ipfs add $resultsFolder/result.tar.gz.minilock').read();
         newHash = newHash.split(" ")[1];
         if newHash == "":
            log("Generated new hash return empty error. Trying again.", 'yellow');
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

   if storageID == '1': #{ #EUDAT
      os.environ['newHash'] = "0x00";
      
      os.system("rm $resultsFolder/.node-xmlhttprequest*");      
      os.chdir(resultsFolder);
      
      # os.popen('find . -type f ! -newer $resultsFolder/modifiedDate.txt -delete'); # Client's loaded files are deleted, no need to re-upload them.
      # log(os.popen('tar -jcvf result-$clusterID-$index.tar.gz *').read());
      log(os.popen('d=$(cat $resultsFolderPrev/modifiedDate.txt); tar -N \'$d\' -jcvf result-$clusterID-$index.tar.gz *').read()); 
      
      res = os.popen('curl -X PUT -H \'Content-Type: text/plain\' -H \'Authorization: Basic \'$encodedShareToken\'==\' --data-binary \'@result-\'$clusterID\'-\'$index\'.tar.gz\' https://b2drop.eudat.eu/public.php/webdav/result-$clusterID-$index.tar.gz').read();
      log(res)

      if '<d:error' in res:
         log('EUDAT repository did not successfully loaded.', 'red')
         sys.exit();      
   #}
   
   elif str(storageID) == '4': #{ #GDRIVE
      os.environ['newHash'] = "0x00";
      mimeType   = os.popen('gdrive info $jobKey -c $GDRIVE_METADATA| grep \'Mime\' | awk \'{print $2}\'').read().rstrip('\n');
      log('mimeType: ' + str(mimeType));         
      os.chdir(resultsFolder);

      if 'folder' in mimeType: # Received job is in folder format
         os.system('find . -type f ! -newer $resultsFolderPrev/modifiedDate.txt -delete'); # Client's loaded files are deleted, no need to re-upload them
         
      res = os.popen('tar -czvf result-$clusterID-$index.tar.gz .').read(); log(res);
      time.sleep(0.25);

      if 'folder' in mimeType: # Received job is in folder format
         log('mimeType: folder');         
         log(os.popen('gdrive upload --parent $jobKey result-$clusterID-$index.tar.gz -c $GDRIVE_METADATA').read());
      elif 'gzip' in mimeType: # Received job is in folder tar.gz
         log('mimeType: tar.gz');
         log(os.popen('gdrive update $jobKey result-$clusterID-$index.tar.gz -c $GDRIVE_METADATA').read());
      elif '/zip' in mimeType: # Received job is in zip format
         log('zip');
         log(os.popen('gdrive update $jobKey result-$clusterID-$index.tar.gz -c $GDRIVE_METADATA').read());
   #}
   
   receiptCheckTx();
   
   # os.system("rm -rf " + programPath + '/' + jobKey + "_" + index); # Deleted downloaded code from local since it is not needed anymore
#}

if __name__ == '__main__': #{
   jobKey      = sys.argv[1];
   index       = sys.argv[2];
   storageID   = sys.argv[3];
   shareToken  = sys.argv[4];
   folderName  = sys.argv[5];

   endCall(jobKey, index, storageID, shareToken, folderName)
#}
