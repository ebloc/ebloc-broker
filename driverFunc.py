#!/usr/bin/env python

from datetime import datetime, timedelta
import owncloud, hashlib, getpass, sys, os, time, subprocess, lib, endCode
from   subprocess import call
import os.path
from colored import stylize
from colored import fg
import subprocess
import glob, errno
from contractCalls.getJobInfo import getJobInfo

jobKeyGlobal = "" 
indexGlobal  = "" 

# Paths===================================================
ipfsHashes       = lib.PROGRAM_PATH 
# =========================================================
os.environ['eblocPath']        = lib.EBLOCPATH 
os.environ['clusterID']        = lib.CLUSTER_ID 

def silentremove(filename): #{
    try:
        os.remove(filename)
    except OSError as e: # This would be "except OSError, e:" before Python 2.6
       pass 
#}

def removeFiles(filename): #{
   if "*" in filename: #{
       for fl in glob.glob(filename):
           print(fl)
           silentremove(fl) 
   #}
   else:
       silentremove(filename) 
#}

def log(strIn, color=''): #{
   if color != '':
       print(stylize(strIn, fg(color))) 
   else:
       print(strIn)
   
   txFile = open(lib.LOG_PATH + '/transactions/clusterOut.txt', 'a') 
   txFile.write(strIn + "\n") 
   txFile.close() 

   fname = lib.LOG_PATH + '/transactions/' + jobKeyGlobal + '_' + indexGlobal + '_driverOutput' +'.txt'      
   txFile = open(fname, 'a') 
   txFile.write(strIn + "\n") 
   txFile.close() 
#}

# checks: does SLURM run on the background or not
def isSlurmOn(): #{
   os.environ['logPath'] = lib.LOG_PATH 
   os.system("bash checkSinfo.sh")  
   check = os.popen("cat $logPath/checkSinfoOut.txt").read()

   if (not "PARTITION" in str(check)) or ("sinfo: error" in str(check)):
      print('slurm is not on.')
      os.system("sudo bash runSlurm.sh") 
#}

def sbatchCall(userID, resultsFolder, eBlocBroker, web3): #{
   os.environ['userID'] = str(userID) 
   os.environ['resultsFolder'] = str(resultsFolder) 
   
   os.system('sudo chown -R $userID .')  # Give permission to user that will send jobs to Slurm.
   
   myDate = os.popen('LANG=en_us_88591 && date --date=\'1 seconds\' +"%b %d %k:%M:%S %Y"').read().rstrip('\n') 
   log(myDate) 
   txFile = open('../modifiedDate.txt', 'w') 
   txFile.write(myDate + '\n' )    
   txFile.close() 
   time.sleep(0.25) 
   
   os.system('sudo su - $userID -c "cp $resultsFolder/run.sh $resultsFolder/${jobKey}*${index}*${storageID}*$shareToken.sh"')    
   jobInfo = getJobInfo(lib.CLUSTER_ID, jobKeyGlobal, int(indexGlobal), eBlocBroker, web3) 
   jobCoreNum    = jobInfo[1] 
   coreSecondGas = timedelta(seconds=int((int(jobInfo[5]) + 1) * 60))  # Client's requested seconds to run his/her job, 1 minute additional given.
   d             = datetime(1,1,1) + coreSecondGas 
   timeLimit     = str(int(d.day)-1) + '-' + str(d.hour) + ':' + str(d.minute) 

   os.environ['timeLimit']  = timeLimit    
   os.environ['jobCoreNum'] = str(jobCoreNum) 
   log("timeLimit: " + str(timeLimit) + "| RequestedCoreNum: " + str(jobCoreNum))  

   # SLURM submit job
   # jobId = os.popen('sudo su - $userID -c "cd $resultsFolder && sbatch -c$jobCoreNum $resultsFolder/${jobKey}*${index}*${storageID}*$shareToken.sh --mail-type=ALL"').read().rstrip('\n')  # Real mode -C is used.
   jobId = os.popen('sudo su - $userID -c "cd $resultsFolder && sbatch -N$jobCoreNum $resultsFolder/${jobKey}*${index}*${storageID}*$shareToken.sh --mail-type=ALL"').read().rstrip('\n')  # Emulator-mode -N is used.   
   jobId = jobId.split()[3] 
   
   os.environ['jobId'] = jobId 
   os.popen('scontrol update jobid=$jobId TimeLimit=$timeLimit') 
   
   if not jobId.isdigit(): #{
      log("Error occured, jobId is not a digit.", 'red')
      return()  # Detects an error on the SLURM side
   #}
#}

def driverGdriveCall(jobKey, index, storageID, userID, eBlocBroker, web3): #{
   global jobKeyGlobal
   global indexGlobal   
   jobKeyGlobal = jobKey  
   indexGlobal  = index 

   log("key: "   + jobKey) 
   log("index: " + index) 

   os.environ['jobKey']          = str(jobKey)
   os.environ['index']           = str(index) 
   os.environ['storageID']       = str(storageID)  
   os.environ['shareToken']      = "-1" 
   os.environ['GDRIVE_METADATA'] = lib.GDRIVE_METADATA 

   resultsFolder     = lib.PROGRAM_PATH + "/" + userID + "/" + jobKey + "_" + index + '/JOB_TO_RUN' 
   os.environ['resultsFolder']     = resultsFolder 
   resultsFolderPrev = lib.PROGRAM_PATH + "/" + userID + "/" + jobKey + "_" + index 
   os.environ['resultsFolderPrev'] = resultsFolderPrev 
   
   if not os.path.isdir(lib.PROGRAM_PATH + "/" + userID + "/" + jobKey + "_" + index): # If folder does not exist
       os.makedirs(lib.PROGRAM_PATH + "/" + userID + "/" + jobKey + "_" + index)
      
   mimeType   = os.popen('gdrive info $jobKey -c $GDRIVE_METADATA | grep \'Mime\' | awk \'{print $2}\'').read().rstrip('\n')
   folderName = os.popen('gdrive info $jobKey -c $GDRIVE_METADATA | grep \'Name\' | awk \'{print $2}\'').read().rstrip('\n') 
   os.environ['folderName']  = folderName 
   log(mimeType) 
   
   if 'folder' in mimeType: #{ # Recieved job is in folder format      
      res = os.popen("gdrive download --recursive $jobKey --force --path $resultsFolderPrev/").read() 
      while ('googleapi: Error 403' in res) or ('googleapi: Error 403: Rate Limit Exceeded, rateLimitExceeded' in res) or ('googleapi' in res and 'error' in res): #{
         time.sleep(10)            
         res = os.popen("gdrive download --recursive $jobKey --force --path $resultsFolderPrev/").read()  # Gets the source code
         log(res)  
      #}      
      log(res)              

      if not os.path.isdir(resultsFolderPrev + '/' + folderName): #{ Check before mv operation.
         log('Folder is not downloaded successfully.', 'red') 
         return 
      #}
      
      os.system("mv $resultsFolderPrev/$folderName $resultsFolder") 

      isTarExist = os.popen("ls -1 $resultsFolder/*.tar.gz 2>/dev/null | wc -l").read() 
      if int(isTarExist) > 0:         
         log(os.popen("tar -xf $resultsFolder/*.tar.gz -C $resultsFolder" ).read())  # This may remove anyother file ending with .tar.gz.

      isZipExist = os.popen("ls -1 $resultsFolder/*.zip 2>/dev/null | wc -l").read() 
      if int(isZipExist) > 0:
         os.system("unzip -j $resultsFolder/*.zip -d $resultsFolder")  # This may remove anyother file ending with .tar.gz.
   #}       
   elif 'gzip' in mimeType: # Recieved job is in folder tar.gz
       os.makedirs(resultsFolder, exist_ok=True)  # Gets the source code     
       os.system("gdrive download $jobKey --force --path $resultsFolder/../")  # Gets the source code
       log(os.popen("tar -xf $resultsFolderPrev/*.tar.gz -C $resultsFolder" ).read()) 
       os.popen("rm -f $resultsFolderPrev/*.tar.gz").read()       
   elif 'zip' in mimeType: # Recieved job is in zip format
       os.makedirs(resultsFolder, exist_ok=True)  # Gets the source code
       os.system("gdrive download $jobKey --force --path $resultsFolderPrev/")  # Gets the source code
       log(os.popen('echo gdrive download --recursive $jobKey --force --path $resultsFolderPrev/').read())
       os.system("unzip -j $resultsFolderPrev/$folderName -d $resultsFolder") 
       os.system("rm -f $resultsFolderPrev/$folderName")       
   else:
       return 

   if os.path.isdir(resultsFolder): # Check before mv operation.
      os.chdir(resultsFolder)       # 'cd' into the working path and call sbatch from there
      sbatchCall(userID, resultsFolder, eBlocBroker, web3)     
#}

def driverGithubCall(jobKey, index, storageID, userID, eBlocBroker, web3): #{
   global jobKeyGlobal
   global indexGlobal   
   jobKeyGlobal = jobKey  
   indexGlobal  = index 

   log("key: "   + jobKey) 
   log("index: " + index)

   os.environ['jobKeyGit']   = str(jobKey).replace("=", "/")
   os.environ['index']       = str(index) 
   os.environ['storageID'] = storageID  
   os.environ['shareToken']  = "-1" 

   resultsFolder     = lib.PROGRAM_PATH + "/" + userID + "/" + jobKey + "_" + index + '/JOB_TO_RUN'
   os.environ['resultsFolder'] = resultsFolder 
   # resultsFolderPrev = lib.PROGRAM_PATH + "/" + userID + "/" + jobKey + "_" + index                  os.environ['resultsFolderPrev'] = resultsFolderPrev 

   if not os.path.isdir(lib.PROGRAM_PATH + "/" + userID + "/" + jobKey + "_" + index): # If folder does not exist
      os.makedirs(lib.PROGRAM_PATH + "/" + userID + "/" + jobKey + "_" + index)
 
   os.system("git clone https://github.com/$jobKeyGit.git $resultsFolder")  # Gets the source code
   os.chdir(resultsFolder)  # 'cd' into the working path and call sbatch from there
   sbatchCall(userID, resultsFolder, eBlocBroker, web3)    
#}

def driverEudatCall(jobKey, index, fID, userID, eBlocBroker, web3): #{
   global jobKeyGlobal
   global indexGlobal   
   jobKeyGlobal = jobKey  
   indexGlobal  = index 
   
   log("key: "   + jobKey) 
   log("index: " + index) 

   os.environ['jobKey']      = str(jobKey) 
   os.environ['index']       = str(index) 
   os.environ['storageID'] = "1" 

   resultsFolder     = lib.PROGRAM_PATH + "/" + userID + "/" + jobKey + "_" + index + '/JOB_TO_RUN' 
   resultsFolderPrev = lib.PROGRAM_PATH + "/" + userID + "/" + jobKey + "_" + index 
   os.environ['resultsFolder']     = resultsFolder    
   os.environ['resultsFolderPrev'] = lib.PROGRAM_PATH + "/" + userID + "/" + jobKey + "_" + index 
      
   f      = open(lib.EBLOCPATH + '/eudatPassword.txt', 'r') # Password is read from the file. password.txt is have only user access
   password = f.read().rstrip('\n').replace(" ", "") 
   f.close()

   log("Login into owncloud" ) 
   oc = owncloud.Client('https://b2drop.eudat.eu/') 
   oc.login('aalimog1@binghamton.edu', password)  # Unlocks EUDAT account

   shareList = oc.list_open_remote_share() 

   acceptFlag      = 0 
   eudatFolderName = "" 
   log("Finding acceptID:")
   for i in range(len(shareList)-1, -1, -1): #{ Starts iterating from last item  to first one
      inputFolderName = shareList[i]['name']
      inputFolderName = inputFolderName[1:] # Removes '/' on the beginning
      inputId         = shareList[i]['id']
      inputOwner      = shareList[i]['owner']
      shareToken      = shareList[i]['share_token']

      if (inputFolderName == jobKey) and (inputOwner == fID): #{
         log("InputId: " + inputId + " |ShareToken: " + shareToken) 
         os.environ['shareToken']      = str(shareToken) 
         os.environ['eudatFolderName'] = str(inputFolderName) 
         eudatFolderName               = inputFolderName 
         acceptFlag = 1 
         break 
      #}
   #}

   if acceptFlag == 0: #{
      oc.logout() 
      log("Couldn't find the shared file", 'red') 
      return 
   #}
   
   if not os.path.isdir(lib.PROGRAM_PATH + "/" + userID + "/" + jobKey + "_" + index): # If folder does not exist
      os.makedirs(lib.PROGRAM_PATH + "/" + userID + "/" + jobKey + "_" + index)
      
   #checkRunExist = os.popen("unzip -l $resultsFolder/output.zip | grep $eudatFolderName/run.sh" ).read()# Checks does zip contains run.sh file
   #if (not eudatFolderName + "/run.sh" in checkRunExist ):
   #log("Error: Folder does not contain run.sh file or client does not run ipfs daemon on the background.")
   #return  #detects error on the SLURM side.

   # TODO: fix ------------------------------------------------------------------------------------------------ # delete   
   # print(os.popen("echo wget -4 -o /dev/stdout https://b2drop.eudat.eu/s/$shareToken/download --output-document=$resultsFolderPrev/output.zip").read()) #delete
   # Downloads shared file as .zip, much faster.
   ret = os.popen("ret=$(wget -4 -o /dev/stdout https://b2drop.eudat.eu/s/$shareToken/download --output-document=$resultsFolderPrev/output.zip)  echo \"$ret\"").read()    
   if "ERROR 404: Not Found" in ret:
       log(ret, 'red') 
       log('File not found The specified document has not been found on the server.', 'red') 
       # TODO: since folder does not exist, do complete refund to the user.
       return  
   print(ret) 
   # ------------------------------------------------------------------------------------------------ # delete  
   time.sleep(0.25)  
   if os.path.isfile(resultsFolderPrev + '/output.zip'): #{
       os.system("unzip -jo $resultsFolderPrev/output.zip -d $resultsFolder") 
       os.system("rm -f $resultsFolderPrev/output.zip")  
   #}
   
   isTarExist = os.popen("ls -1 $resultsFolder/*.tar.gz 2>/dev/null | wc -l").read() 
   if int(isTarExist) > 0: #{
      os.popen("bash $eblocPath/tar.sh $resultsFolder" ).read()  # Extracting all *.tar.gz files.      
      os.popen("rm -f $resultsFolder/*.tar.gz").read()  # Removing all tar.gz files after extraction is done.
   #}
   
   isZipExist = os.popen("ls -1 $resultsFolder/*.zip 2>/dev/null | wc -l").read()
   if int(isZipExist) > 0: #{
      log(os.popen("" ).read()) 
      os.system("unzip -jo $resultsFolderPrev/$jobKey -d $resultsFolder") 
      os.system("rm -f $resultsFolder/*.zip")  
   #}
   
   os.chdir(resultsFolder)  # 'cd' into the working path and call sbatch from there
   sbatchCall(userID, resultsFolder, eBlocBroker, web3) 
#}

def driverIpfsCall(jobKey, index, storageID, userID, eBlocBroker, web3): #{
    global jobKeyGlobal
    global indexGlobal   
    jobKeyGlobal = jobKey  
    indexGlobal  = index 
    
    lib.isIpfsOn(os, time) 
    os.environ['jobKey']     = jobKey 
    os.environ['index']      = str(index) 
    os.environ['storageID']  = str(storageID) 
    os.environ['shareToken'] = "-1" 
    os.environ['userID']     = userID 
        
    resultsFolder = lib.PROGRAM_PATH + "/" + userID + "/" + jobKey + "_" + index + '/JOB_TO_RUN' 
    os.environ['resultsFolder'] = resultsFolder 
    resultsFolderPrev = lib.PROGRAM_PATH + "/" + userID + "/" + jobKey + "_" + index     
   
    log("jobKey: " + jobKey) 

    if not os.path.isdir(resultsFolderPrev): # If folder does not exist
       os.makedirs(resultsFolderPrev, exist_ok=True) 
       os.makedirs(resultsFolder,     exist_ok=True) 

    os.chdir(resultsFolder)  # 'cd' into the working path and call sbatch from there
    
    if os.path.isfile(jobKey):
       os.system('rm -f $jobKey')     

    ipfsCallCounter = 0 
    isIPFSHashExist = os.popen("bash $eblocPath/ipfsStat.sh $jobKey").read() 

    log(isIPFSHashExist) 
    
    if "CumulativeSize" in isIPFSHashExist: #{
       os.system('bash $eblocPath/ipfsGet.sh $jobKey $resultsFolder') 
       if storageID == '2': #{ Case for the ipfsMiniLock
          os.environ['passW'] = 'bright wind east is pen be lazy usual' 
          log(os.popen('mlck decrypt -f $resultsFolder/$jobKey --passphrase="$passW" --output-file=$resultsFolder/output.tar.gz').read()) 

          os.system('rm -f $resultsFolder/$jobKey') 
          os.system('tar -xf $resultsFolder/output.tar.gz && rm -f $resultsFolder/output.tar.gz') 
       #}
       
       if not os.path.isfile('run.sh'): 
          log("run.sh does not exist", 'red') 
          return 
    else:
       log("!!!!!!!!!!!!!!!!!!!!!!! Markle not found! timeout for ipfs object stat retrieve !!!!!!!!!!!!!!!!!!!!!!!", 'red')  # IPFS file could not be accessed
       return 
    #}
    sbatchCall(userID, resultsFolder, eBlocBroker, web3) 
#}

# To test driverFunc.py executed as script.
if __name__ == '__main__': #{
   #var        = "3d8e2dc2-b855-1036-807f-9dbd8c6b1579=QmVvHrWzVmK3VASrGax7czDwfavwjgXgGmoeYRJtU6Az99" 
   #index      = "0" 
   #driverEudatCall(var, index) 
   #------
   var        = "QmefdYEriRiSbeVqGvLx15DKh4WqSMVL8nT4BwvsgVZ7a5"
   index      = "1"
   myType     = "0"

   driverIpfsCall(var, index, myType) 
#}
