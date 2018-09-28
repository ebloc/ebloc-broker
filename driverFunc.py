#!/usr/bin/env python

import owncloud, hashlib, getpass, sys, os, time, subprocess, lib, endCode, zipfile
from datetime import datetime, timedelta
from   subprocess import call
import os.path
from colored import stylize
from colored import fg
import subprocess
import glob, errno
from contractCalls.getJobInfo import getJobInfo

jobKeyGlobal    = '' 
indexGlobal     = ''
storageIDGlobal = ''
shareTokenGlobal = '-1'

# Paths===================================================
ipfsHashes       = lib.PROGRAM_PATH 
# =========================================================

def silentremove(filename): #{
    try:
        os.remove(filename)
    except OSError as e: # This would be "except OSError, e:" before Python 2.6
       pass
#}

def removeFiles(filename): #{
   if "*" in filename: 
       for fl in glob.glob(filename):
           print(fl)
           silentremove(fl) 
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

def cache(cacheType): #{
    if cacheType is 'local': # Download into local directory at $HOME/.eBlocBroker/cache
        x = 1
    elif cacheType is 'ipfs':
        x = 1
#}
    
def sbatchCall(userID, resultsFolder, eBlocBroker, web3): #{
   # Give permission to user that will send jobs to Slurm.
   subprocess.run(['sudo', 'chown', '-R', userID, '.'])

   # cmd: date --date=1 seconds +%b %d %k:%M:%S %Y
   date = subprocess.check_output(['date', '--date=' + '1 seconds', '+%b %d %k:%M:%S %Y'],
                                  env={'LANG': 'en_us_88591'}).decode('utf-8').strip()
   log('Date=' + date)
   f = open('../modifiedDate.txt', 'w') 
   f.write(date + '\n' )    
   f.close()

   # echo date | date +%s
   p1 = subprocess.Popen(['echo', date], stdout=subprocess.PIPE)
   #-----------
   p2 = subprocess.Popen(['date', '+%s'], stdin=p1.stdout, stdout=subprocess.PIPE)
   p1.stdout.close()
   #-----------
   timestamp = p2.communicate()[0].decode('utf-8').strip()
   log('Timestamp=' + timestamp)

   f = open('../timestamp.txt', 'w') 
   f.write(timestamp + '\n' )    
   f.close()
   
   time.sleep(0.25)    
   # cmd: sudo su - $userID -c "cp $resultsFolder/run.sh $resultsFolder/${jobKey}*${index}*${storageID}*$shareToken.sh
   subprocess.run(['sudo', 'su', '-', userID, '-c',
                   'cp ' + resultsFolder + '/run.sh ' +
                   resultsFolder + '/' + jobKeyGlobal + '*' + str(indexGlobal) + '*' + str(storageIDGlobal) + '*' + shareTokenGlobal + '.sh']);
                            
   jobInfo = getJobInfo(lib.CLUSTER_ID, jobKeyGlobal, int(indexGlobal), eBlocBroker, web3)
   jobCoreNum    = str(jobInfo['core'])
   coreSecondGas = timedelta(seconds=int((jobInfo['coreMinuteGas'] + 1) * 60))  # Client's requested seconds to run his/her job, 1 minute additional given.
   d             = datetime(1,1,1) + coreSecondGas 
   timeLimit     = str(int(d.day)-1) + '-' + str(d.hour) + ':' + str(d.minute) 

   log("timeLimit: " + str(timeLimit) + "| RequestedCoreNum: " + jobCoreNum)  

   # cmd: sudo su - $userID -c "cd $resultsFolder && sbatch -c$jobCoreNum $resultsFolder/${jobKey}*${index}*${storageID}*$shareToken.sh --mail-type=ALL
   # SLURM submit job, Real mode -N is used. For Emulator-mode -N use 'sbatch -c'
   jobID = subprocess.check_output(['sudo', 'su', '-', userID, '-c',
                                    'cd' + ' ' + resultsFolder + ' && ' + 'sbatch -N' + jobCoreNum + ' ' + 
                                    resultsFolder + '/' + jobKeyGlobal + '*' + str(indexGlobal) + '*' + str(storageIDGlobal) + '*' + shareTokenGlobal + '.sh' + ' ' + 
                                    '--mail-type=ALL']).decode('utf-8').strip()
   jobID = jobID.split()[3]
   log('jobID=' + jobID) # delete
   try:
       # cmd: scontrol update jobid=$jobID TimeLimit=$timeLimit
       subprocess.run(['scontrol', 'update', 'jobid=' + jobID, 'TimeLimit=' + timeLimit], stderr=subprocess.STDOUT)
   except subprocess.CalledProcessError as e:
       log(e.output.decode('utf-8').strip())
      
   if not jobID.isdigit(): #{
      log("Error occured, jobID is not a digit.", 'red')
      return()  # Detects an error on the SLURM side
   #}
#}

def driverGdriveCall(jobKey, index, storageID, userID, eBlocBroker, web3): #{
   global jobKeyGlobal
   global indexGlobal
   global storageIDGlobal
   global shareTokenGlobal
   
   jobKeyGlobal = jobKey  
   indexGlobal  = index 
   storageIDGlobal = storageID
   
   log("key: "   + jobKey) 
   log("index: " + index) 

   resultsFolder     = lib.PROGRAM_PATH + "/" + userID + "/" + jobKey + "_" + index + '/JOB_TO_RUN' 
   resultsFolderPrev = lib.PROGRAM_PATH + "/" + userID + "/" + jobKey + "_" + index 
   
   if not os.path.isdir(lib.PROGRAM_PATH + "/" + userID + "/" + jobKey + "_" + index): # If folder does not exist
       os.makedirs(lib.PROGRAM_PATH + "/" + userID + "/" + jobKey + "_" + index)

   #cmd: gdrive info $jobKey -c $GDRIVE_METADATA # stored for both pipes otherwise its read and lost   
   gdriveInfo = subprocess.check_output(['gdrive', 'info', jobKey, '-c', lib.GDRIVE_METADATA]).decode('utf-8').strip() 
   
   # cmd: echo gdriveInfo | grep \'Mime\' | awk \'{print $2}\'
   p1 = subprocess.Popen(['echo', gdriveInfo], stdout=subprocess.PIPE)
   #-----------
   p2 = subprocess.Popen(['grep', 'Mime'], stdin=p1.stdout, stdout=subprocess.PIPE)
   # p1.stdout.close() delete
   #-----------
   p3 = subprocess.Popen(['awk', '{print $2}'], stdin=p2.stdout,stdout=subprocess.PIPE)
   p2.stdout.close()
   #-----------
   mimeType = p3.communicate()[0].decode('utf-8').strip()

   # cmd: echo gdriveInfo | grep \'Name\' | awk \'{print $2}\'
   p1 = subprocess.Popen(['echo', gdriveInfo], stdout=subprocess.PIPE)
   #-----------
   p2 = subprocess.Popen(['grep', 'Name'], stdin=p1.stdout, stdout=subprocess.PIPE)
   p1.stdout.close()
   #-----------
   p3 = subprocess.Popen(['awk', '{print $2}'], stdin=p2.stdout,stdout=subprocess.PIPE)
   p2.stdout.close()
   #-----------
   folderName = p3.communicate()[0].decode('utf-8').strip()
   
   log(mimeType) 
   
   if 'folder' in mimeType: #{ # Recieved job is in folder format      
      # cmd: gdrive download --recursive $jobKey --force --path $resultsFolderPrev  # Gets the source 
      res= subprocess.check_output(['gdrive', 'download', '--recursive', jobKey, '--force', '--path', resultsFolderPrev]).decode('utf-8')
      flag = 1
      while ('googleapi: Error 403' in res) or ('googleapi: Error 403: Rate Limit Exceeded, rateLimitExceeded' in res) or ('googleapi' in res and 'error' in res):
         time.sleep(10)            
         # cmd: gdrive download --recursive $jobKey --force --path $resultsFolderPrev  # Gets the source 
         res= subprocess.check_output(['gdrive', 'download', '--recursive', jobKey, '--force', '--path', resultsFolderPrev]).decode('utf-8').strip()
         log(res)
         flag = 0
         
      if flag is 1:
          log(res)       
      if not os.path.isdir(resultsFolderPrev + '/' + folderName): #{ Checking before mv operation
         log('Folder is not downloaded successfully.', 'red') 
         return 
      #}      
      # cmd: mv $resultsFolderPrev/$folderName $resultsFolder
      subprocess.run(['mv', resultsFolderPrev + '/folderName', resultsFolder])
      
      if glob.glob(resultsFolder + '/*.tar.gz'): #{  check file ending in .tar.gz exist
         # cmd: tar -xf $resultsFolder/*.tar.gz -C $resultsFolder
         # Remove any file ending with .tar.gz.
         for tarFile in glob.glob(resultsFolder + '/*.tar.gz'):
             subprocess.run(['tar', '-xf', tarFile, '-C', resultsFolder])

      if glob.glob(resultsFolder + '/*.zip'): #{  check file ending in .zip exist         
         # cmd: unzip -j $resultsFolder/*.zip -d $resultsFolder
         # This may remove anyother file ending with .zip
         for zipFile in glob.glob(resultsFolder + '/*.zip'):
             subprocess.run(['unzip', '-j', zipFile, '-d', resultsFolder])         
   #}       
   elif 'gzip' in mimeType: # Recieved job is in folder tar.gz
       os.makedirs(resultsFolder, exist_ok=True)  # Gets the source code     
       # cmd: gdrive download $jobKey --force --path $resultsFolder/../
       subprocess.run(['gdrive', 'download', jobKey, '--force', '--path', resultsFolderPrev + '/../']) # Gets the source code       
       # cmd: tar -xf $resultsFolderPrev/*.tar.gz -C $resultsFolder
       log(subprocess.check_output(['tar', '-xf'] + glob.glob(resultsFolderPrev + '/*.tar.gz') + ['C', resultsFolder]).decode('utf-8'))       
       # cmd: rm -f $resultsFolderPrev/*.tar.gz
       subprocess.run(['rm', '-f'] + glob.glob(resultsFolderPrev + '/*.tar.gz'))
   elif 'zip' in mimeType: # Recieved job is in zip format
       os.makedirs(resultsFolder, exist_ok=True)  # Gets the source code
       # cmd: gdrive download $jobKey --force --path $resultsFolderPrev/
       subprocess.run(['gdrive', 'download', jobKey, '--force', '--path', resultsFolderPrev]) # Gets the source code
       log('gdrive download --recursive ' + jobKey + '--force --path ' + resultsFolderPrev)
       # cmd: unzip -j $resultsFolderPrev/$folderName -d $resultsFolder
       subprocess.run(['unzip', '-j', resultsFolderPrev + '/' + folderName, '-d', resultsFolder])       
       # cmd: rm -f $resultsFolderPrev/$folderName
       subprocess.run(['rm', '-rf', resultsFolderPrev + '/' + folderName])
   else:
       return 

   if os.path.isdir(resultsFolder): # Check before mv operation.
      os.chdir(resultsFolder)       # 'cd' into the working path and call sbatch from there
      sbatchCall(userID, resultsFolder, eBlocBroker, web3)     
#}

def driverGithubCall(jobKey, index, storageID, userID, eBlocBroker, web3): #{
   global jobKeyGlobal
   global indexGlobal
   global storageIDGlobal
   global shareTokenGlobal

   jobKeyGlobal    = jobKey  
   indexGlobal     = index 
   storageIDGlobal = storageID
   jobKeyGit       = str(jobKey).replace("=", "/")
   
   log("key: "   + jobKey) 
   log("index: " + index)

   resultsFolder     = lib.PROGRAM_PATH + "/" + userID + "/" + jobKey + "_" + index + '/JOB_TO_RUN'
   # resultsFolderPrev = lib.PROGRAM_PATH + "/" + userID + "/" + jobKey + "_" + index

   if not os.path.isdir(lib.PROGRAM_PATH + "/" + userID + "/" + jobKey + "_" + index): # If folder does not exist
      os.makedirs(lib.PROGRAM_PATH + "/" + userID + "/" + jobKey + "_" + index)

   # cmd: git clone https://github.com/$jobKeyGit.git $resultsFolder
   subprocess.run(['git', 'clone', 'https://github.com/' + jobKeyGit + '.git', resultsFolder]) # Gets the source code   
   os.chdir(resultsFolder)  # 'cd' into the working path and call sbatch from there
   sbatchCall(userID, resultsFolder, eBlocBroker, web3)    
#}

def driverEudatCall(jobKey, index, fID, userID, eBlocBroker, web3): #{
   global jobKeyGlobal
   global indexGlobal
   global storageIDGlobal
   global shareTokenGlobal

   jobKeyGlobal = jobKey  
   indexGlobal  = index 
   storageIDGlobal = '1'
      
   log("key: "   + jobKey) 
   log("index: " + index) 

   resultsFolder     = lib.PROGRAM_PATH + "/" + userID + "/" + jobKey + "_" + index + '/JOB_TO_RUN' 
   resultsFolderPrev = lib.PROGRAM_PATH + "/" + userID + "/" + jobKey + "_" + index 

   with open(lib.EBLOCPATH + '/eudatPassword.txt', 'r') as content_file:
       password = content_file.read().strip()

   log("Login into owncloud" ) 
   oc = owncloud.Client('https://b2drop.eudat.eu/') 
   oc.login('aalimog1@binghamton.edu', password)  # Unlocks EUDAT account
   password = None   
   shareList = oc.list_open_remote_share() 

   acceptFlag      = 0 
   eudatFolderName = "" 
   log("Finding acceptID:")
   for i in range(len(shareList)-1, -1, -1): #{ Starts iterating from last item  to first one
      inputFolderName  = shareList[i]['name']
      inputFolderName  = inputFolderName[1:] # Removes '/' on the beginning
      inputId          = shareList[i]['id']
      inputOwner       = shareList[i]['owner']
      shareToken       = shareList[i]['share_token']
      shareTokenGlobal = shareList[i]['share_token']
      
      if (inputFolderName == jobKey) and (inputOwner == fID): #{
         log("InputId: " + inputId + " |ShareToken: " + shareToken) 
         shareTokenGlobal              = str(shareToken)
         eudatFolderName               = str(inputFolderName)
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
      
   '''
   # cmd: unzip -l $resultsFolder/output.zip | grep $eudatFolderName/run.sh
   # Checks does zip contains run.sh file
   p1 = subprocess.Popen(['unzip', '-l', resultsFolder + '/output.zip'], stdout=subprocess.PIPE)
   #-----------
   p2 = subprocess.Popen(['grep', eudatFolderName + '/run.sh'], stdin=p1.stdout, stdout=subprocess.PIPE)
   p1.stdout.close()
   #-----------
   out = p2.communicate()[0].decode('utf-8').strip()   
   if not '/run.sh' in out:
       log("Error: Folder does not contain run.sh file.")
       return  
   '''   
   # Downloads shared file as .zip, much faster.
   # cmd: wget -4 -o /dev/stdout https://b2drop.eudat.eu/s/$shareToken/download --output-document=$resultsFolderPrev/output.zip
   ret = subprocess.check_output(['wget', '-4', '-o', '/dev/stdout', 'https://b2drop.eudat.eu/s/' + shareToken +
                                  '/download', '--output-document=' + resultsFolderPrev + '/output.zip']).decode('utf-8')
   if "ERROR 404: Not Found" in ret:
       log(ret, 'red') 
       log('File not found The specified document has not been found on the server.', 'red') 
       # TODO: since folder does not exist, do complete refund to the user.
       return  
   print(ret) 

   time.sleep(0.25)  
   if os.path.isfile(resultsFolderPrev + '/output.zip'): #{
       subprocess.run(['unzip', '-jo', resultsFolderPrev + '/output.zip', '-d', resultsFolder])
       subprocess.run(['rm', '-f', resultsFolderPrev + '/output.zip'])
   #}
   
   if glob.glob(resultsFolder + '/*.tar.gz'): #{  check file ending in .tar.gz exist
      # Extracting all *.tar.gz files.
      subprocess.run(['bash', lib.EBLOCPATH + '/tar.sh', resultsFolder])      
      # Removing all tar.gz files after extraction is done.
      subprocess.run(['rm', '-f'] + glob.glob(resultsFolder + '/*.tar.gz'))
   #}
   
   if glob.glob(resultsFolder + '/*.zip'): #{  check file ending in .zip exist
      subprocess.run(['unzip', '-jo', resultsFolderPrev + '/' + jobKey, '-d', resultsFolder])
      subprocess.run(['rm', '-f'] + glob.glob(resultsFolder + "/*.zip"))
   #}
   
   os.chdir(resultsFolder)  # 'cd' into the working path and call sbatch from there
   sbatchCall(userID, resultsFolder, eBlocBroker,  web3) 
#}

def driverIpfsCall(jobKey, index, storageID, userID, eBlocBroker, web3): #{
    global jobKeyGlobal
    global indexGlobal
    global storageIDGlobal
    global shareTokenGlobal
    
    jobKeyGlobal = jobKey  
    indexGlobal  = index
    storageIDGlobal = storageID
    
    lib.isIpfsOn() 
        
    resultsFolder = lib.PROGRAM_PATH + "/" + userID + "/" + jobKey + "_" + index + '/JOB_TO_RUN' 
    resultsFolderPrev = lib.PROGRAM_PATH + "/" + userID + "/" + jobKey + "_" + index     
   
    log("jobKey: " + jobKey) 

    if not os.path.isdir(resultsFolderPrev): # If folder does not exist
       os.makedirs(resultsFolderPrev, exist_ok=True) 
       os.makedirs(resultsFolder,     exist_ok=True) 

    os.chdir(resultsFolder)  # 'cd' into the working path and call sbatch from there
    
    if os.path.isfile(jobKey):
       subprocess.run(['rm', '-f', jobKey])

    ipfsCallCounter = 0
    while True: #{
        try:
            # cmd: timeout 300 ipfs object stat $jobKey
            # IPFS_PATH=$HOME"/.ipfs" && export IPFS_PATH TODO: Probably not required
            isIPFSHashExist = subprocess.check_output(['timeout', '300', 'ipfs', 'object', 'stat', jobKey]).decode('utf-8').strip() # Wait Max 5 minutes.
            log(isIPFSHashExist)
            break
        except subprocess.CalledProcessError as e: # Catches resource temporarily unavailable on ipfs
            log(e.output.decode('utf-8').strip(), 'red')
            if ipfsCallCounter == 5:
                return
            ipfsCallCounter += 1
            time.sleep(10)
    #}    
    if "CumulativeSize" in isIPFSHashExist: #{
       # cmd: ipfs get $jobKey --output=$resultsFolder
       # IPFS_PATH=$HOME"/.ipfs" && export IPFS_PATH TODO: Probably not required
       res = subprocess.check_output(['ipfs', 'get', jobKey, '--output='+resultsFolder]).decode('utf-8').strip() # Wait Max 5 minutes.
       print(res)
              
       if storageID == '2': #{ Case for the ipfsMiniLock
          passW = 'bright wind east is pen be lazy usual' 

          # cmd: mlck decrypt -f $resultsFolder/$jobKey --passphrase="$passW" --output-file=$resultsFolder/output.tar.gz
          log(subprocess.check_output(['mlck', 'decrypt', '-f', resultsFolder + '/' + jobKey +
                                       '--passphrase=' + passW,
                                       '--output-file=' + resultsFolder + '/output.tar.gz']).decode('utf-8'))          
          # cmd: rm -f $resultsFolder/$jobKey
          subprocess.run(['rm', '-f', resultsFolder + '/' + jobKey])         
          # cmd: tar -xf $resultsFolder/output.tar.gz
          subprocess.run(['tar', '-xf', resultsFolder + '/output.tar.gz'])          
          # cmd: rm -f $resultsFolder/output.tar.gz
          subprocess.run(['rm', '-f', resultsFolder + '/output.tar.gz'])
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
   var        = "QmefdYEriRiSbeVqGvLx15DKh4WqSMVL8nT4BwvsgVZ7a5"
   index      = "1"
   myType     = "0"

   driverIpfsCall(var, index, myType) 
#}
