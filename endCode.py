#!/usr/bin/env python

import sys, os, time, subprocess, lib, base64, glob

from subprocess import call
from colored import stylize
from colored import fg
import hashlib
from imports import connectEblocBroker
from imports import getWeb3

sys.path.insert(0, './contractCalls')
from contractCalls.getJobInfo   import getJobInfo
from contractCalls.getUserInfo  import getUserInfo
from contractCalls.receiptCheck import receiptCheck

jobKeyGlobal = "" 
indexGlobal  = "" 

web3        = getWeb3()
eBlocBroker = connectEblocBroker(web3)

def log(strIn, color=''): #{
   if color != '':
      print(stylize(strIn, fg(color))) 
   else:
      print(strIn)

   txFile = open(lib.LOG_PATH + '/endCodeAnalyse/' + jobKeyGlobal + "_" + indexGlobal + '.txt', 'a') 
   txFile.write(strIn + "\n")  
   txFile.close() 
#}

def receiptCheckTx(jobKey, index, elapsedRawTime, newHash, storageID, jobID): #{
   # cmd: scontrol show job jobID | grep 'EndTime'| grep -o -P '(?<=EndTime=).*(?= )'
   p1 = subprocess.Popen(['scontrol', 'show', 'job', jobID], stdout=subprocess.PIPE)
   #-----------
   p2 = subprocess.Popen(['grep', 'EndTime'], stdin=p1.stdout, stdout=subprocess.PIPE)
   p1.stdout.close()
   #-----------
   p3 = subprocess.Popen(['grep', '-o', '-P', '(?<=EndTime=).*(?= )'], stdin=p2.stdout,stdout=subprocess.PIPE)
   p2.stdout.close()
   date      = p3.communicate()[0].decode('utf-8').strip()
   # cmd: date -d 2018-09-09T21:50:51 +"%s"
   endTimeStamp = subprocess.check_output(["date", "-d", date, '+\'%s\'']).strip().decode('utf-8').replace("\'","")   
   log("endTimeStamp: " + endTimeStamp) 
     
   txHash = receiptCheck(jobKey, index, elapsedRawTime, newHash, storageID, endTimeStamp, eBlocBroker, web3)
   while txHash == "notconnected" or txHash == "": #{
      log("Error: Please run geth on the background.", 'red')

      log(jobKey + ' ' + index + ' ' + elapsedRawTime + ' ' + newHash + ' ' + storageID + ' ' + endTimeStamp) 
      txHash = receiptCheck(jobKey, index, elapsedRawTime, newHash, storageID, endTimeStamp, eBlocBroker, web3)
      time.sleep(5) 
   #}
   
   log("receiptCheck " + txHash)  
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
   programPath           = lib.PROGRAM_PATH    
   os.environ['logPath'] = lib.LOG_PATH 
   os.environ['GDRIVE']  = lib.GDRIVE 
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
      
   jobInfo = getJobInfo(clusterAddress, jobKey, index, eBlocBroker, web3)
   
   # while jobInfo == "Connection refused" or jobInfo == "" or jobInfo == "Errno" : #{
   while not jobInfo:      
      log('jobInfo: ' + jobInfo) 

      log('getJobInfo.py ' + ' ' + clusterAddress + ' ' + jobKey + ' ' + index)
      log("Error: Please run geth on the background.", 'red')
      jobInfo = getJobInfo(clusterAddress, jobKey, index, eBlocBroker, web3)
      time.sleep(5)
   #}

   log("JOB_INFO: " + ",".join(map(str, jobInfo)))

   userID     = jobInfo[6].replace("u'", "").replace("'", "").lower()
   userIDAddr = hashlib.md5(userID.encode('utf-8')).hexdigest()  # Convert Ethereum User Address into 32-bits
   userInfo   = getUserInfo(userID, '1', eBlocBroker, web3)

   resultsFolder     = programPath + "/" + userIDAddr + "/" + jobKey + "_" + index + '/JOB_TO_RUN' 
   resultsFolderPrev = programPath + "/" + userIDAddr + "/" + jobKey + "_" + index 
   os.environ['resultsFolder']     = resultsFolder 
   os.environ['resultsFolderPrev'] = resultsFolderPrev

   subprocess.run(['rm', '-f'] + glob.glob(resultsFolder + '/result-*tar.gz'))  

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

   log("\njobOwner's Info: ")  
   log('{0: <13}'.format('userEmail: ')     + userInfo[1])
   log('{0: <13}'.format('miniLockID: ')    + userInfo[2])
   log('{0: <13}'.format('ipfsAddress: ')   + userInfo[3])
   log('{0: <13}'.format('fID: ')           + userInfo[4])
   os.environ['clientMiniLockId']  = userInfo[2] 
      
   log("") 
   
   if jobInfo[0] == str(lib.job_state_code['COMPLETED']): #{
      log('Job is already get paid.', 'red') 
      sys.exit() 
   #}

   clientTimeLimit = jobInfo[5] 
   log("clientGasMinuteLimit: " + str(clientTimeLimit))  # Clients minuteGas for the job
   
   countTry = 0 
   while True: #{      
      #if countTry > 200: # setJobStatus may deploy late.
      #   sys.exit()
      countTry += 1                  
      log("Waiting... " + str(countTry * 60) + ' seconds passed.', 'yellow')  
      if jobInfo[0] == lib.job_state_code['RUNNING']: # It will come here eventually, when setJob() is deployed.
         log("Job has been started.", 'green')  
         break  # Wait until does values updated on the blockchain
      
      if jobInfo[0] == lib.job_state_code['COMPLETED']: 
        log("Error: Already completed job is received.", 'red')  
        sys.exit()  # Detects an error on the SLURM side

      jobInfo = getJobInfo(clusterAddress, jobKey, index, eBlocBroker, web3)
      #while jobInfo == "Connection refused" or jobInfo == "" or jobInfo == "Errno" : #{
      while not jobInfo:      
         log("Error: Please run geth on the background.", 'red')
         jobInfo = getJobInfo(clusterAddress, jobKey, index, eBlocBroker, web3)
         time.sleep(5)
      #}      
      time.sleep(60) # Short sleep here so this loop is not keeping CPU busy
   #}
   
   log("jobName: " + str(folderName))    
   # cmd: scontrol show job $jobID > $resultsFolder/slurmJobInfo.out
   with open(resultsFolder + '/slurmJobInfo.out', 'w') as stdout:
      subprocess.Popen(['scontrol', 'show', 'job', jobID], stdout=stdout)
   
   # Here we know that job is already completed 
   if str(storageID) == '0' or str(storageID) == '3': #{ IPFS or GitHub
      # Uploaded as folder
      newHash = subprocess.check_output(['ipfs', 'add', '-r', resultsFolder]).strip().decode('utf-8')      
      countTry = 0 
      while newHash == "": #{
         if (countTry > 10):
            sys.exit()
         countTry += 1
         '''
         # Approach to upload as .tar.gz. Currently not used.
         os.popen('find . -type f ! -newer $resultsFolderPrev/modifiedDate.txt -delete')  # Not needed, already uploaded files won't uploaded again.         
         with open(resultsFolderPrev + '/modifiedDate.txt') as content_file:
            date = content_file.read().strip()
         log(subprocess.check_output(['tar', '-N', date, '-jcvf', 'result-' + lib.CLUSTER_ID + '-' + str(index) + '.tar.gz' ] + glob.glob("*")).decode('utf-8'))                     
         newHash = res = subprocess.check_output(['ipfs', 'add', resultsFolder + '/result.tar.gz']).strip().decode('utf-8')
         newHash = newHash.split(' ')[1]
         subprocess.run(['rm', '-f', resultsFolder + '/result.tar.gz'])
         '''
         log("Generated new hash return empty error. Trying again...", 'yellow')
         newHash = subprocess.check_output(['ipfs', 'add', '-r', resultsFolder]).strip().decode('utf-8')      
         time.sleep(5) 
      #}
         
      # cmd: echo newHash | tail -n1 | awk '{print $2}'
      p1 = subprocess.Popen(['echo', text], stdout=subprocess.PIPE)
      #-----------
      p2 = subprocess.Popen(['tail', '-n1'], stdin=p1.stdout, stdout=subprocess.PIPE)
      p1.stdout.close()
      #-----------
      p3 = subprocess.Popen(['awk', '{print $2}'], stdin=p2.stdout,stdout=subprocess.PIPE)
      p2.stdout.close()
      #-----------
      newHash = p3.communicate()[0].decode('utf-8').strip()
      log("newHash: " + newHash)        
   #}
   if str(storageID) == '2': #{ IPFS & miniLock
      os.chdir(resultsFolder) 

      with open(resultsFolderPrev + '/modifiedDate.txt') as content_file:
         date = content_file.read().strip()
      log(subprocess.check_output(['tar', '-N', date, '-jcvf', 'result-' + lib.CLUSTER_ID + '-' + str(index) + '.tar.gz' ] + glob.glob("*")).decode('utf-8'))            
     
      log(os.popen('mlck encrypt -f $resultsFolder/result.tar.gz $clientMiniLockId --anonymous --output-file=$resultsFolder/result.tar.gz.minilock').read()) 
      # os.system('find $resultsFolder -type f ! -newer $resultsFolder/modifiedDate.txt -delete') 

      newHash = res = subprocess.check_output(['ipfs', 'add', resultsFolder + '/result.tar.gz.minilock']).strip().decode('utf-8')
      newHash = newHash.split(' ')[1]
      countTry = 0 
      while newHash == "": #{
         if countTry > 10:
            sys.exit()
         countTry += 1                   
         log("Generated new hash return empty error. Trying again.", 'yellow')
         newHash = res = subprocess.check_output(['ipfs', 'add', resultsFolder + '/result.tar.gz.minilock']).strip().decode('utf-8')
         newHash = newHash.split(' ')[1]
         time.sleep(5) 
      #}      
      log("newHash: " + newHash)       
   #}
      
   elapsedTime = os.popen('sacct -n -X -j $jobID --format="Elapsed"').read() 
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

   log("finalizedElapsedRawTime: " + str(elapsedRawTime)) 
   log("jobInfo: " + str(jobInfo)) 

   if storageID == '1': #{ #EUDAT
      newHash = '0x00'
      # cmd: rm $resultsFolder/.node-xmlhttprequest*
      subprocess.run(['rm', '-f'] + glob.glob(resultsFolder + '/.node-xmlhttprequest*'))
      os.chdir(resultsFolder) 
      
      # os.popen('find . -type f ! -newer $resultsFolder/modifiedDate.txt -delete')  # Client's loaded files are removed, no need to re-upload them.
      # log(os.popen('tar -jcvf result-$clusterID-$index.tar.gz *').read())

      with open(resultsFolderPrev + '/modifiedDate.txt') as content_file:
         date = content_file.read().strip()
      log(subprocess.check_output(['tar', '-N', date, '-jcvf', 'result-' + lib.CLUSTER_ID + '-' + str(index) + '.tar.gz' ] + glob.glob("*")).decode('utf-8'))            
      
      res = os.popen('curl -X PUT -H \'Content-Type: text/plain\' -H \'Authorization: Basic \'$encodedShareToken\'==\' --data-binary \'@result-\'$clusterID\'-\'$index\'.tar.gz\' https://b2drop.eudat.eu/public.php/webdav/result-$clusterID-$index.tar.gz').read() 
      log(res)

      if '<d:error' in res:
         log('EUDAT repository did not successfully loaded.', 'red')
         sys.exit()       
   #}   
   elif str(storageID) == '4': #{ #GDRIVE
      newHash = '0x00'
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

      with open(f, resultsFolderPrev + '/modifiedDate.txt') as content_file:
         date = content_file.read().strip()
      log(subprocess.check_output(['tar', '-N', date, '-jcvf', 'result-' + lib.CLUSTER_ID + '-' + str(index) + '.tar.gz' ] + glob.glob("*")).decode('utf-8'))            
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
   receiptCheckTx(jobKey, index, elapsedRawTime, newHash, storageID, jobID)

   # Removed downloaded code from local since it is not needed anymore
   subprocess.run(['rm', '-rf', programPath + '/' + jobKey + "_" + index])
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
