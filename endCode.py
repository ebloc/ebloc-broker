#!/usr/bin/env python

from subprocess import call
import sys, os, time, subprocess, constants, base64

jobKeyGlobal = "";
indexGlobal  = "";

def logTest(strIn):
   print(strIn)        
   txFile = open( constants.LOG_PATH + '/endCodeAnalyse/' + jobKeyGlobal + "_" + indexGlobal + '.txt', 'a') # Folder should not created as root user
   txFile.write(strIn + "\n"); 
   txFile.close();

def endCall(jobKey, index, storageType, shareToken, miniLockId, folderName):
   endTimeStamp = os.popen( 'date +%s' ).read(); 

   global jobKeyGlobal; jobKeyGlobal=jobKey
   global indexGlobal;  indexGlobal=index;  

   os.environ['endTimeStamp'] = endTimeStamp; # Get endTimeStamp right away
   logTest( "endTimeStamp: " + endTimeStamp )

   eblocPath         = constants.EBLOCPATH
   logPath           = constants.LOG_PATH
   programPath       = constants.PROGRAM_PATH 
   encodedShareToken = base64.b64encode( shareToken + ':' )

   header = "var mylib = require('" + eblocPath + "/eBlocHeader.js')"; os.environ['header']     = header;

   os.environ['programPath']       = str(programPath)
   os.environ['cluster_id']        = constants.CLUSTER_ID
   os.environ['jobKey']            = jobKey
   os.environ['index']             = str(index)
   os.environ["IPFS_PATH"]         = constants.IPFS_REPO # Default IPFS repo path
   os.environ['eblocPath']         = eblocPath
   os.environ['encodedShareToken'] = encodedShareToken
   os.environ['clientMiniLockId']  = miniLockId
   os.environ['jobName']           = folderName
   os.environ['storageType']       = str(storageType)

   fDate = open( programPath + '/' + jobKey + "_" + index + '/modifiedDate.txt', 'r')
   modifiedDate = fDate.read().replace("\n", "")
   os.environ['modifiedDate'] = modifiedDate; fDate.close()
   logTest( modifiedDate )

   logTest( "keyHash: "            + jobKey                 )
   logTest( "Index: "              + index                  )
   logTest( "storageType: "        + storageType            )
   logTest( "shareToken: |"        + shareToken        + "|")
   logTest( "encodedShareToken: |" + encodedShareToken + "|")
   logTest( "miniLockId: |"        + miniLockId        + "|")

   jobInfo = os.popen('node $eblocPath/eBlocBrokerNodeCall.js getJobInfo $cluster_id $jobKey $index').read().replace("\n", "").replace(" ", "");  

   while(True):
      if( not(jobInfo == "notconnected" or jobInfo == "") ): 
         break;
      else:
         logTest("Error: Please run Parity or Geth on the background.**************************************************************")
         jobInfo = os.popen('node $eblocPath/eBlocBrokerNodeCall.js getJobInfo $cluster_id $jobKey $index').read().replace("\n", "").replace(" ", "");  
      time.sleep(1)

   logTest( "JOB_INFO:" + jobInfo)
   jobInfo = jobInfo.split(',');
   timeout = time.time() + 3 * 60   # Timeout threshold is three minutes from now

   logTest( "0: " + jobInfo[0] )
   logTest( "1: " + jobInfo[2] )

   while True:
      logTest( jobInfo[0] ); 
      logTest( jobInfo[2] ); 

      clientTimeLimit = jobInfo[5];
      logTest( "TimeLimit: " + clientTimeLimit ); 

      if jobInfo[0] == str( constants.job_state_code['RUNNING'] ):
         break; # Wait until does values updated on the blockchain

      if time.time() > timeout:
         break
      
      if jobInfo[0] == constants.job_state_code['COMPLETED']: 
        logTest(  "Error: Already completed job..."); 
        sys.exit(); # Detects an error on the SLURM side

      jobInfo = os.popen('node $eblocPath/eBlocBrokerNodeCall.js getJobInfo $cluster_id $jobKey $index').read().replace("\n", "").replace(" ", ""); 
      while(True):
         if( not(jobInfo == "notconnected" or jobInfo == "") ): 
            break;
         else:
            logTest("Error: Please run Parity or Geth on the background.**************************************************************")
            jobInfo = os.popen('node $eblocPath/eBlocBrokerNodeCall.js getJobInfo $cluster_id $jobKey $index').read().replace("\n", "").replace(" ", ""); 
         time.sleep(1)

      jobInfo = jobInfo.split(',');
      time.sleep(5) # Short sleep here so this loop is not keeping CPU busy

   jobId = os.popen( "sacct --name $jobName.sh  -n | awk '{print $1}' | head -n 1 | sed -r 's/[.batch]+//g' " ).read();
   os.environ['jobId'] = jobId;
   logTest( "JOBID------------> " + str(jobId) );

   # Here we know that job is already completed
   if str(storageType) == '0':
      countTry=0;
      while(True): 
         if (countTry > 10):
            sys.exit()
         countTry = countTry + 1         

         logTest( "IPFS add started: " + programPath + " " + jobKey + " " + index );
         os.popen( 'find . -type f ! -newer $encrypyFolderPath/modifiedDate.txt -delete' )           

         newHash = os.popen( 'ipfs add -r ' + programPath + '/${jobKey}_$index' ).read();  

         if (newHash == ""):
            logTest("Generated new hash return empty error. Trying again");
         else:
            os.environ['newHash'] = newHash;
            newHash               = os.popen( 'echo $newHash | tr " " "\n" | tail -n2 | head -n1'  ).read().replace("\n", ""); 
            os.environ['newHash'] = newHash;
            logTest( "newHash: " + newHash); 
            break

   if str(storageType) == '2':
      encrypyFolderPath = programPath + "/" + jobKey + "_" + index;
      os.environ['encrypyFolderPath'] = encrypyFolderPath
      logTest( "encrypyFolderPath: " + encrypyFolderPath )

      os.chdir( encrypyFolderPath )
      res = os.popen( 'tar -P -cvzf $encrypyFolderPath/result.tar.gz .' ).read();
      logTest( "tarRes: " + res )

      res = os.popen( 'mlck encrypt -f $encrypyFolderPath/result.tar.gz $clientMiniLockId --anonymous --output-file=$encrypyFolderPath/result.tar.gz.minilock' ).read();
      logTest(  "IPFS-miniLock add started: " + programPath + " " + jobKey + " " + index );           
      os.popen( 'find $encrypyFolderPath -type f ! -newer $encrypyFolderPath/modifiedDate.txt -delete' )

      countTry = 0;
      while(True): 
         if (countTry > 10):
            sys.exit()
         countTry = countTry + 1                  
         
         newHash = os.popen( 'ipfs add $encrypyFolderPath/result.tar.gz.minilock' ).read();
         logTest( "newHash: " + newHash ) 
         newHash = newHash.split(" ")[1];

         if (newHash == ""):
            logTest("Generated new hash return empty error. Trying again.");
         else:
            os.environ['newHash'] = newHash;
            newHash               = os.popen( 'echo $newHash | tr " " "\n" | tail -n2 | head -n1'  ).read().replace("\n", ""); 
            os.environ['newHash'] = newHash;
            logTest( "newHash: " + newHash);
            break;

   logTest( "jobId: "   + jobId);
   elapsedTime = os.popen('sacct -j $jobId --format="Elapsed" | tail -n1 | head -n1' ).read();
   logTest( "ElapsedTime: " + elapsedTime );

   elapsedTime = elapsedTime.split(':');

   elapsedDay     = "0";
   elapsedHour    = elapsedTime[0].replace(" ", "");
   elapsedMinute  = elapsedTime[1].rstrip();
   elapsedSeconds = elapsedTime[2].rstrip();

   if "-" in str(elapsedHour):
      logTest( elapsedHour )
      elapsedHour = elapsedHour.split('-');
      elapsedDay  = elapsedHour[0];
      elapsedHour = elapsedHour[1];

   logTest(str(int(elapsedDay))     );     
   logTest(str(int(elapsedHour))    );    
   logTest(str(int(elapsedMinute))  );  
   logTest(str(int(elapsedSeconds)) ); 

   elapsedRawTime = int(elapsedDay)* 1440 + int(elapsedHour) * 60 + int(elapsedMinute) + 1;
   logTest( "ElapsedRawTime: " + str(elapsedRawTime) )

   if( elapsedRawTime > int(clientTimeLimit) ):
      elapsedRawTime = clientTimeLimit

   os.environ['elapsedRawTime'] = str(elapsedRawTime);
   logTest( "ElapsedRawTime: " + str(elapsedRawTime) )
   logTest( "jobInfo: " + str(jobInfo) )

   if storageType == '0' or storageType == '2':                         
      transactionHash = os.popen('node $eblocPath/eBlocBrokerNodeCall.js receiptCheck $jobKey $index $elapsedRawTime $newHash $storageType $endTimeStamp').read().replace("\n", "").replace(" ", ""); 
      while(True):
         if (not(transactionHash == "notconnected" or transactionHash == "")): 
            break;
         else:
            logTest("Error: Please run Parity or Geth on the background.**************************************************************")
            transactionHash = os.popen('node $eblocPath/eBlocBrokerNodeCall.js receiptCheck $jobKey $index $elapsedRawTime $newHash $storageType $endTimeStamp').read().replace("\n", "").replace(" ", ""); 
         time.sleep(5)
   elif storageType == '1':
      nullByte="0x00"; os.environ['nullByte'] = nullByte
      transactionHash = os.popen('node $eblocPath/eBlocBrokerNodeCall.js receiptCheck $jobKey $index $elapsedRawTime $nullByte $storageType  $endTimeStamp').read().replace("\n", "").replace(" ", ""); 
      while(True):
         if (not(transactionHash == "notconnected" or transactionHash == "")): 
            break;
         else:
            logTest("Error: Please run Parity or Geth on the background.**************************************************************")
            transactionHash = os.popen('node $eblocPath/eBlocBrokerNodeCall.js receiptCheck $jobKey $index $elapsedRawTime $nullByte $storageType $endTimeStamp').read().replace("\n", "").replace(" ", ""); 
         time.sleep(5)

      jobKeyTemp = jobKey.split('=');
      folderName = jobKeyTemp[1]
      logTest( folderName )

      localEudatPath = programPath + '/' + jobKey + "_" + index;
      os.environ['localEudatPath'] = localEudatPath

      os.system( "rm $localEudatPath/.node-xmlhttprequest*" )

      os.chdir(localEudatPath) 
      os.popen( 'find . -type f ! -newer $localEudatPath/modifiedDate.txt -delete' ) # Client's loaded files are deleted, no need to re-upload them
      os.popen( 'zip -r results.zip .' ) 
      res = os.popen( 'curl -X PUT -H \'Content-Type: text/plain\' -H \'Authorization: Basic \'$encodedShareToken\'==\' --data-binary \'@results.zip\' https://b2drop.eudat.eu/public.php/webdav/results.zip' ).read()
      logTest(res); 
      #os.system( "rm -rf " + programPath + '/' + jobKey + "_" + index ); # Deleted downloaded code from local since it is not needed anymore

   logTest( "ReceiptHash: " + transactionHash ); 
   txFile = open( logPath + '/transactions/'   + constants.CLUSTER_ID + '.txt', 'a');   
   txFile.write( transactionHash + " end_receiptCheck\n" );
   txFile.close();

if __name__ == '__main__': #py_driver.py executed as script
   jobKey      = sys.argv[1];
   index       = sys.argv[2];
   storageType = sys.argv[3];
   shareToken  = sys.argv[4];
   miniLockId  = sys.argv[5];
   runName     = sys.argv[6];

   endCall( jobKey, index, storageType, shareToken, miniLockId, runName )


#delete old code:
#out = os.popen(' find . -type f -newermt \'' + modifiedDate + '\' -exec cp -v --parents {} ' + constants.OWN_CLOUD_PATH + '/' + folderName + ' \;' ).read(); 
#print( out ); 
#f.write( out );       
#oc.decline_remote_share(storageType)  
