#!/usr/bin/env python

from subprocess import call
import sys, os, time, subprocess, lib, base64
from colored import stylize
from colored import fg
import hashlib
from imports import connectEblocBroker
from imports import getWeb3

sys.path.insert(0, './contractCalls')
from contractCalls.getJobInfo import getJobInfo

jobKeyGlobal = "" 
indexGlobal  = "" 

eBlocBroker = connectEblocBroker()
web3        = getWeb3()

def log(strIn, color=''): #{
   if color != '':
      print(stylize(strIn, fg(color))) 
   else:
      print(strIn)

   txFile = open(lib.LOG_PATH + '/endCodeAnalyse/' + jobKeyGlobal + "_" + indexGlobal + '.txt', 'a') 
   txFile.write(strIn + "\n")  
   txFile.close() 
#}

def receiptCheckTx(jobKey, index): #{
   endTimeStamp = os.popen('date -d $(scontrol show job $jobID | grep \'EndTime\'| grep -o -P \'(?<=EndTime=).*(?= )\') +"%s"').read().rstrip('\n') 
   os.environ['endTimeStamp'] = endTimeStamp 
   log("endTimeStamp: " + endTimeStamp) 
     
   txHash = os.popen('. $eblocPath/venv/bin/activate && $eblocPath/venv/bin/python3 $contractCallPath/receiptCheck.py $jobKey $index $elapsedRawTime $newHash $storageID $endTimeStamp  2>/dev/null').read().rstrip('\n')    
   while txHash == "notconnected" or txHash == "": #{
      log("Error: Please run geth on the background.", 'red')
      print(os.popen('echo $jobKey $index $elapsedRawTime $newHash $storageID $endTimeStamp').read().rstrip('\n')) 

      txHash = os.popen('. $eblocPath/venv/bin/activate && $eblocPath/venv/bin/python3 $contractCallPath/receiptCheck.py $jobKey $index $elapsedRawTime $newHash $storageID $endTimeStamp  2>/dev/null').read().rstrip('\n') 
      time.sleep(5) 
   #}
   
   log("ReceiptHash: " + txHash)  
   txFile = open(lib.LOG_PATH + '/transactions/' + lib.CLUSTER_ID + '.txt', 'a') 

   txFile.write(jobKey + "_" + index + "| Tx: " + txHash + "| receiptCheckTx\n") 
   txFile.close() 
#}

def endCall(jobKey, index, storageID, shareToken, folderName, jobID): #{
   global jobKeyGlobal
   global indexGlobal   
   jobKeyGlobal = jobKey  
   indexGlobal  = index 
   
   log('endCode.py ' + jobKey + ' ' + index + ' ' + storageID + ' ' + shareToken + ' ' + folderName + ' ' + jobID) 
   log("jobID: " + jobID) 

   if jobKey == index:
      log('JobKey and index are same.', 'red') 
      sys.exit() 
      
   os.environ['jobID'] = jobID    
   
   # Paths--------------------------------------
   contractCallPath      = lib.EBLOCPATH + '/contractCalls'  
   programPath           = lib.PROGRAM_PATH    
   os.environ['logPath'] = lib.LOG_PATH 
   os.environ['GDRIVE']  = lib.GDRIVE 
   os.environ['contractCallPath'] = contractCallPath 
   # -------------------------------------------   
   encodedShareToken = '' 
   if shareToken != '-1':      
      encodedShareToken = base64.b64encode((str(shareToken) + ':').encode('utf-8')).decode('utf-8') 

   log("encodedShareToken: " + encodedShareToken) 

   clusterAddress = lib.CLUSTER_ID;
   
   os.environ['programPath']       = str(programPath) 
   os.environ['clusterID']         = lib.CLUSTER_ID 
   os.environ['GDRIVE_METADATA']   = lib.GDRIVE_METADATA 
   os.environ['jobKey']            = jobKey 
   os.environ['index']             = str(index) 
   os.environ["IPFS_PATH"]         = lib.IPFS_REPO  # Default IPFS repo path
   os.environ['eblocPath']         = lib.EBLOCPATH 
   os.environ['encodedShareToken'] = encodedShareToken   
   os.environ['jobName']           = folderName 
   os.environ['storageID']         = str(storageID)    
      
   jobInfo = getJobInfo(clusterAddress, jobKey, index, eBlocBroker, web3)
   # os.popen('. $eblocPath/venv/bin/activate && $eblocPath/venv/bin/python3 $contractCallPath/getJobInfo.py $clusterID $jobKey $index 2>/dev/null').read().rstrip('\n').replace(" ","")[1:-1]  delete

   while jobInfo == "Connection refused" or jobInfo == "" or jobInfo == "Errno" : #{
      log('jobInfo: ' + jobInfo) 
      log(getJobInfo(clusterAddress, jobKey, index, eBlocBroker, web3))
      # log(os.popen('echo $contractCallPath/getJobInfo.py $clusterID $jobKey $index').read().rstrip('\n')) 
      log("Error: Please run geth on the background.", 'red')
      jobInfo = os.popen('. $eblocPath/venv/bin/activate && $eblocPath/venv/bin/python3 $contractCallPath/getJobInfo.py $clusterID $jobKey $index 2>/dev/null').read().rstrip('\n').replace(" ","")[1:-1]          
      time.sleep(5)
   #}

   log("JOB_INFO:" + jobInfo)
   jobInfo = jobInfo.split(',') 

   userIDAddr = hashlib.md5(jobInfo[6].replace("u'", "").replace("'", "").encode('utf-8')).hexdigest()  # Convert Ethereum User Address into 32-bits
   os.environ['userID'] = jobInfo[6].replace("u'", "").replace("'", "") 
   userInfo = os.popen('. $eblocPath/venv/bin/activate && $eblocPath/venv/bin/python3 $contractCallPath/getUserInfo.py $userID 1').read().rstrip('\n').replace(" ", "") 

   resultsFolder     = programPath + "/" + userIDAddr + "/" + jobKey + "_" + index + '/JOB_TO_RUN' 
   resultsFolderPrev = programPath + "/" + userIDAddr + "/" + jobKey + "_" + index 
   os.environ['resultsFolder']     = resultsFolder 
   os.environ['resultsFolderPrev'] = resultsFolderPrev 
   os.system('rm -f $resultsFolder/result-*tar.gz')

   log("\nwhoami: "          + os.popen('whoami').read().rstrip('\n')) 
   log("pwd: "               + os.popen('pwd').read().rstrip('\n')) 
   log("resultsFolder: "     + resultsFolder) 
   log("jobKey: "            + jobKey) 
   log("index: "             + index) 
   log("storageID: "         + storageID) 
   log("shareToken: "        + shareToken) 
   log("encodedShareToken: " + encodedShareToken)    
   log("folderName: "        + folderName) 
   log("clusterID: "         + lib.CLUSTER_ID) 
   log("userIDAddr: "        + userIDAddr)    

   if os.path.isfile(resultsFolderPrev + '/modifiedDate.txt'): #{
      fDate = open(resultsFolderPrev + '/modifiedDate.txt', 'r')
      modifiedDate = fDate.read().rstrip('\n') 
      os.environ['modifiedDate'] = modifiedDate 
      fDate.close() 
      log(modifiedDate) 
   #}

   if ',' in userInfo: #{
      userInfo = userInfo.split(',') 
      log("jobOwner's Info: ")  
      log('{0: <13}'.format('userEmail: ')     + userInfo[1])
      log('{0: <13}'.format('miniLockID: ')    + userInfo[2])
      log('{0: <13}'.format('ipfsAddress: ')   + userInfo[3])
      log('{0: <13}'.format('fID: ')           + userInfo[4])
      os.environ['clientMiniLockId']  = userInfo[2] 
   #}
   else:     
      log("userInfo split Failure", 'red')
      
   log("") 
   
   if jobInfo[0] == str(lib.job_state_code['COMPLETED']): #{
      log('Job is already get paid.', 'red') 
      sys.exit() 
   #}

   clientTimeLimit = jobInfo[5] 
   log("clientGasMinuteLimit: " + clientTimeLimit)  # Clients minuteGas for the job
      
   countTry = 0 
   while True: #{      
      #if countTry > 200: # setJobStatus may deploy late.
      #   sys.exit()
      countTry += 1                  
      log("Waiting... " + str(countTry * 60) + ' seconds passed.', 'yellow')  
      if jobInfo[0] == str(lib.job_state_code['RUNNING']): # It will come here eventually, when setJob() is deployed.
         log("Job has been started to run.", 'green')  
         break  # Wait until does values updated on the blockchain
      
      if jobInfo[0] == lib.job_state_code['COMPLETED']: 
        log("Error: Already completed job is received.", 'red')  
        sys.exit()  # Detects an error on the SLURM side

      jobInfo = os.popen('. $eblocPath/venv/bin/activate && $eblocPath/venv/bin/python3 $contractCallPath/getJobInfo.py $clusterID $jobKey $index 2>/dev/null').read().rstrip('\n').replace(" ","")[1:-1]          
      while jobInfo == "Connection refused" or jobInfo == "" or jobInfo == "Errno" : #{
         log("Error: Please run geth on the background.", 'red')
         jobInfo = os.popen('. $eblocPath/venv/bin/activate && $eblocPath/venv/bin/python3 $contractCallPath/getJobInfo.py $clusterID $jobKey $index 2>/dev/null').read().rstrip('\n').replace(" ","")[1:-1]          
         time.sleep(5)
      #}      
      jobInfo = jobInfo.split(',') 
      time.sleep(60) # Short sleep here so this loop is not keeping CPU busy
   #}
   
   log("jobName: " + str(folderName)) 
   
   os.system('scontrol show job $jobID > $resultsFolder/slurmJobInfo.out') 
   
   # Here we know that job is already completed 
   if str(storageID) == '0' or str(storageID) == '3': #{ IPFS or GitHub
      newHash = os.popen('ipfs add -r $resultsFolder').read()  # Upload as folder.      
      countTry = 0 
      while newHash == "": #{
         if (countTry > 10):
            sys.exit()
         countTry += 1         
         
         # os.popen('find . -type f ! -newer $resultsFolderPrev/modifiedDate.txt -delete')  # Not needed, already uploaded files won't uploaded again.         
         # log(os.popen('d=$(cat $resultsFolderPrev/modifiedDate.txt); tar -N \'$d\' -jcvf result.tar.gz *').read())  #| 
         # newHash = os.popen('ipfs add ' + resultsFolder + '/result.tar.gz').read()                                  #| Upload as .tar.gz.
         # log(os.popen('rm -f $resultsFolder/result.tar.gz').read())  #un-comment                                    #|
         log("Generated new hash return empty error. Trying again...", 'yellow') 
         newHash = os.popen('ipfs add -r $resultsFolder').read()  # upload as files.
         time.sleep(5) 
      #}
         
      os.environ['newHash'] = newHash 
      newHash = os.popen('echo $newHash | tr " " "\n" | tail -n2 | head -n1' ).read().rstrip('\n')  
      os.environ['newHash'] = newHash 
      log("newHash: " + newHash)        
   #}
   if str(storageID) == '2': #{ IPFS & miniLock
      os.chdir(resultsFolder) 
      log(os.popen('d=$(cat $resultsFolderPrev/modifiedDate.txt);  tar -N \"$d\" -jcvf result.tar.gz *').read()) 

      log(os.popen('mlck encrypt -f $resultsFolder/result.tar.gz $clientMiniLockId --anonymous --output-file=$resultsFolder/result.tar.gz.minilock').read()) 
      # os.system('find $resultsFolder -type f ! -newer $resultsFolder/modifiedDate.txt -delete') 

      newHash = os.popen('ipfs add $resultsFolder/result.tar.gz.minilock').read()       
      countTry = 0 
      while newHash == "": #{
         if countTry > 10:
            sys.exit()
         countTry += 1                   
         log("Generated new hash return empty error. Trying again.", 'yellow') 
         newHash = os.popen('ipfs add $resultsFolder/result.tar.gz.minilock').read() 
         time.sleep(5) 
      #}
      
      newHash = newHash.split(" ")[1] 
      os.environ['newHash'] = newHash 
      newHash = os.popen('echo $newHash | tr " " "\n" | tail -n2 | head -n1' ).read().rstrip('\n')
      os.environ['newHash'] = newHash 
      log("newHash: " + newHash) 
      
   #}
      
   elapsedTime = os.popen('sacct -j $jobID --format="Elapsed" | tail -n1 | head -n1').read() 
   log("ElapsedTime: " + elapsedTime) 

   elapsedTime    = elapsedTime.split(':') 
   elapsedDay     = "0" 
   elapsedHour    = elapsedTime[0].replace(" ", "") 
   elapsedMinute  = elapsedTime[1].rstrip() 
   elapsedSeconds = elapsedTime[2].rstrip() 

   if "-" in str(elapsedHour):
      elapsedHour = elapsedHour.split('-') 
      elapsedDay  = elapsedHour[0] 
      elapsedHour = elapsedHour[1] 

   elapsedRawTime = int(elapsedDay)* 1440 + int(elapsedHour) * 60 + int(elapsedMinute) + 1 
   log("ElapsedRawTime: " + str(elapsedRawTime))

   if elapsedRawTime > int(clientTimeLimit):
      elapsedRawTime = clientTimeLimit 

   os.environ['elapsedRawTime'] = str(elapsedRawTime) 
   log("finalizedElapsedRawTime: " + str(elapsedRawTime)) 
   log("jobInfo: " + str(jobInfo)) 

   if storageID == '1': #{ #EUDAT
      os.environ['newHash'] = "0x00" 
      
      os.system("rm $resultsFolder/.node-xmlhttprequest*")       
      os.chdir(resultsFolder) 
      
      # os.popen('find . -type f ! -newer $resultsFolder/modifiedDate.txt -delete')  # Client's loaded files are removed, no need to re-upload them.
      # log(os.popen('tar -jcvf result-$clusterID-$index.tar.gz *').read())       
      log(os.popen('d=$(cat $resultsFolderPrev/modifiedDate.txt); tar -N \"$d\" -jcvf result-$clusterID-$index.tar.gz *').read())  
      
      res = os.popen('curl -X PUT -H \'Content-Type: text/plain\' -H \'Authorization: Basic \'$encodedShareToken\'==\' --data-binary \'@result-\'$clusterID\'-\'$index\'.tar.gz\' https://b2drop.eudat.eu/public.php/webdav/result-$clusterID-$index.tar.gz').read() 
      log(res)

      if '<d:error' in res:
         log('EUDAT repository did not successfully loaded.', 'red')
         sys.exit()       
   #}   
   elif str(storageID) == '4': #{ #GDRIVE
      os.environ['newHash'] = "0x00" 
      
      mimeType = os.popen('$GDRIVE info $jobKey -c $GDRIVE_METADATA| grep \'Mime\' | awk \'{print $2}\'').read().rstrip('\n') 
      countTry=0 
      while mimeType == "": #{
         if countTry > 10: # mimeType may just return empty string, lets try few more time...
            sys.exit()                        
         log('mimeType returns empty string. Try: ' + str(countTry), 'red')            
         mimeType = os.popen('$GDRIVE info $jobKey -c $GDRIVE_METADATA| grep \'Mime\' | awk \'{print $2}\'').read().rstrip('\n')             
         countTry += 1 
         time.sleep(15)          
      #}      
      log('mimeType: ' + str(mimeType)) 
               
      os.chdir(resultsFolder) 

      #if 'folder' in mimeType: # Received job is in folder format
      #   os.system('find . -type f ! -newer $resultsFolderPrev/modifiedDate.txt -delete')  # Client's loaded files are removed, no need to re-upload them

      log(os.popen('d=$(cat $resultsFolderPrev/modifiedDate.txt); tar -N \"$d\" -jcvf result-$clusterID-$index.tar.gz *').read())    
      time.sleep(0.25) 

      if 'folder' in mimeType: # Received job is in folder format
         log('mimeType: folder')          
         log(os.popen('$GDRIVE upload --parent $jobKey result-$clusterID-$index.tar.gz -c $GDRIVE_METADATA').read()) 
      elif 'gzip' in mimeType: # Received job is in folder tar.gz
         log('mimeType: tar.gz') 
         log(os.popen('$GDRIVE update $jobKey result-$clusterID-$index.tar.gz -c $GDRIVE_METADATA').read()) 
      elif '/zip' in mimeType: # Received job is in zip format
         log('zip') 
         log(os.popen('$GDRIVE update $jobKey result-$clusterID-$index.tar.gz -c $GDRIVE_METADATA').read()) 
      else:
         log('Files could not be uploaded', 'red')
         sys.exit() 
   #}
   
   receiptCheckTx(jobKey, index)    
   # os.system("rm -rf " + programPath + '/' + jobKey + "_" + index)  # Removed downloaded code from local since it is not needed anymore
#}

if __name__ == '__main__': #{
   jobKey      = sys.argv[1] 
   index       = sys.argv[2] 
   storageID   = sys.argv[3] 
   shareToken  = sys.argv[4] 
   folderName  = sys.argv[5] 
   jobID       = sys.argv[6] 

   endCall(jobKey, index, storageID, shareToken, folderName, jobID)
#}
