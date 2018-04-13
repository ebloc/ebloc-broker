#!/usr/bin/env python

from datetime import datetime, timedelta
import owncloud, hashlib, getpass, sys, os, time, subprocess, constants, endCode
from   subprocess import call
import os.path

jobKeyGlobal = "";
indexGlobal  = "";

# Paths---------
contractCallPath = constants.EBLOCPATH + '/contractCalls'; os.environ['contractCallPath'] = contractCallPath;
ipfsHashes       = constants.PROGRAM_PATH;
# ---------------
os.environ['eblocPath'] = constants.EBLOCPATH;
os.environ['clusterID'] = constants.CLUSTER_ID

def log(strIn): #{
   print(strIn);
   txFile = open(constants.LOG_PATH + '/transactions/clusterOut.txt', 'a');
   txFile.write(strIn + "\n");
   txFile.close();

   fname = constants.LOG_PATH + '/transactions/' + jobKeyGlobal + '_' + indexGlobal + '_driverOutput' +'.txt';     
   txFile = open(fname, 'a');
   txFile.write(strIn + "\n");
   txFile.close();

#}

def contractCall(val): #{
   printFlag=1;
   ret = os.popen(val + "| node").read().rstrip('\n').replace(" ", "");
   while(True):
      if not(ret == "notconnected" or ret == ""):
         break;
      else:
         if (printFlag == 1):
            log("Error: Please run Parity or Geth on the background.**************************************************************")
            printFlag = 0;
            ret = os.popen(val + "| node").read().rstrip('\n').replace(" ", "");
            time.sleep(1);
   return ret;
#}

# checks: does SLURM run on the background or not
def isSlurmOn(): #{
   os.environ['logPath'] = constants.LOG_PATH;
   os.system("bash checkSinfo.sh")  
   check = os.popen("cat $logPath/checkSinfoOut.txt").read()

   if (not "PARTITION" in str(check)) or ("sinfo: error" in str(check)):
      print('slurm is not on.')
      os.system("sudo bash runSlurm.sh");
#}

# checks: does IPFS run on the background or not
def isIpfsOn(): #{
   check = os.popen("ps aux | grep \'[i]pfs daemon\' | wc -l").read().rstrip('\n');
   if (int(check) == 0):
      log("Error: IPFS does not work on the background. Running:\nipfs daemon &");
      os.system("bash " + constants.EBLOCPATH + "/runIPFS.sh");
      time.sleep(5);
      os.system("cat ipfs.out");
   else:
      log("IPFS is already on");
#}

def sbatchCall(): #{
   myDate = os.popen('LANG=en_us_88591 && date +"%b %d %k:%M:%S:%N %Y"' ).read().rstrip('\n'); log(myDate);
   txFile = open('modifiedDate.txt', 'w');
   txFile.write(myDate + '\n' );   
   txFile.close();
   time.sleep(0.25);

   os.system("cp run.sh ${jobKey}_${index}_${folderIndex}_${shareToken}_$miniLockId.sh");
   
   jobInfo = os.popen('$contractCallPath/getJobInfo.py $clusterID $jobKey $index 2>/dev/null').read().rstrip('\n').replace(" ","")[1:-1];         
   jobInfo = jobInfo.split(',');

   jobCoreNum    = jobInfo[1];
   coreSecondGas = timedelta(seconds=int(int(jobInfo[5]) * 60)); # Client's requested seconds to run his/her job
   d             = datetime(1,1,1) + coreSecondGas;
   timeLimit     = str(int(d.day)-1) + '-' + str(d.hour) + ':' + str(d.minute); os.environ['timeLimit'] = timeLimit;   

   os.environ['jobCoreNum'] = jobCoreNum;
   log("timeLimit: " + str(timeLimit) + "| RequestedCoreNum: " + str(jobCoreNum)); 

   # SLURM submit job
   jobId = os.popen('sbatch -N$jobCoreNum $ipfsHashes/${jobKey}_$index/JOB_TO_RUN/${jobKey}_${index}_${folderIndex}_${shareToken}_$miniLockId.sh --mail-type=ALL | cut -d " " -f4-').read().rstrip('\n');
   os.environ['jobId'] = jobId;  
   os.popen('scontrol update jobid=$jobId TimeLimit=$timeLimit');
   
   if not jobId.isdigit():
      log("Error occured, jobId is not a digit.")
      return(); # Detects an error on the SLURM side
#}

#------------------------------------------------------------------------------

def driverGdriveCall(jobKey, index, folderType): #{
   global jobKeyGlobal; jobKeyGlobal = jobKey
   global indexGlobal;  indexGlobal  = index;

   log("key: "   + jobKey);
   log("index: " + index);

   os.environ['jobKey']      = str(jobKey)
   os.environ['index']       = str(index);
   os.environ['ipfsHashes']  = str(ipfsHashes);
   os.environ['folderIndex'] = folderType; 
   os.environ['shareToken']  = "-1";
   os.environ['miniLockId']  = "-1";

   resultsFolder = ipfsHashes + '/' + jobKey + "_" + index;
   os.environ['resultsFolder'] = resultsFolder;
   
   if not os.path.isdir(resultsFolder): # If folder does not exist
      os.makedirs(resultsFolder)

   mimeType = os.popen('gdrive info $jobKey | grep \'Mime\' | awk \'{print $2}\'').read().rstrip('\n');
   if 'folder' in mimeType:
      folderName = os.popen('gdrive info $jobKey | grep \'Name\' | awk \'{print $2}\'').read().rstrip('\n');
      os.environ['folderName']  = folderName;
      os.system("gdrive download --recursive $jobKey --force --path $resultsFolder"); # Gets the source code      
      os.system("mv $resultsFolder/$folderName $resultsFolder/JOB_TO_RUN");
   elif 'gzip' in mimeType:
      print('gzip');

   os.chdir(resultsFolder + '/JOB_TO_RUN');
   sbatchCall();    
#}

def driverGithubCall(jobKey, index, folderType): #{
   global jobKeyGlobal; jobKeyGlobal = jobKey
   global indexGlobal;  indexGlobal  = index;

   log("key: "   + jobKey);
   log("index: " + index)

   os.environ['jobKeyGit']   = str(jobKey).replace("=", "/")
   os.environ['index']       = str(index);
   os.environ['ipfsHashes']  = str(ipfsHashes);
   os.environ['folderIndex'] = folderType; 
   os.environ['shareToken']  = "-1";
   os.environ['miniLockId']  = "-1";

   resultsFolder = ipfsHashes + '/' + jobKey + "_" + index; os.environ['resultsFolder'] = resultsFolder;
   
   if not os.path.isdir(resultsFolder): # If folder does not exist
      os.makedirs(resultsFolder);
 
   os.system("git clone https://github.com/$jobKeyGit.git $resultsFolder/JOB_TO_RUN"); # Gets the source code
   os.chdir(resultsFolder + '/JOB_TO_RUN');
   sbatchCall(); 
#}

def driverEudatCall(jobKey, index): #{
   global jobKeyGlobal; jobKeyGlobal = jobKey
   global indexGlobal;  indexGlobal  = index;

   log("key: "   + jobKey)
   log("index: " + index)

   os.environ['jobKey']      = str(jobKey);
   os.environ['index']       = str(index);
   os.environ['ipfsHashes']  = str(ipfsHashes);
   os.environ['folderIndex'] = "1";
   os.environ['miniLockId']  = "-1";

   jobKeyTemp = jobKey.split('=');
   owner      = jobKeyTemp[0];
   folderName = jobKeyTemp[1];
   header     = "var eBlocBroker = require('" + constants.EBLOCPATH + "/eBlocBrokerHeader.js')"; os.environ['header'] = header;

   f        = open(constants.EBLOCPATH + '/eudatPassword.txt', 'r') # Password is read from the file. password.txt is have only user access
   password = f.read().rstrip('\n').replace(" ", "");
   f.close()

   log("Login into owncloud");
   oc = owncloud.Client('https://b2drop.eudat.eu/');
   oc.login('aalimog1@binghamton.edu', password); # Unlocks EUDAT account
   shareList = oc.list_open_remote_share();

   log("finding_acceptId")
   acceptFlag      = 0;
   eudatFolderName = "";
   for i in range(len(shareList)-1, -1, -1): # Starts iterating from last item  to first one
      inputFolderName = shareList[i]['name']
      inputFolderName = inputFolderName[1:] # Removes '/' on the beginning
      inputId         = shareList[i]['id']
      inputOwner      = shareList[i]['owner']
      shareToken      = shareList[i]['share_token']

      if (inputFolderName == folderName) and (inputOwner == owner):
         log("InputId:_" + inputId + "_ShareToken:_" + shareToken)
         os.environ['shareToken']      = str(shareToken);
         os.environ['eudatFolderName'] = str(inputFolderName);
         eudatFolderName               = inputFolderName;
         acceptFlag = 1;
         break;

   if acceptFlag == 0:
      oc.logout()
      log("Couldn't find the shared file");
      return;

   resultsFolder = ipfsHashes + '/' + jobKey + "_" + index; os.environ['resultsFolder'] = resultsFolder;

   if not os.path.isdir(resultsFolder): # If folder does not exist
      os.makedirs(resultsFolder)

   os.popen("wget https://b2drop.eudat.eu/s/$shareToken/download --output-document=$resultsFolder/output.zip").read() # Downloads shared file as .zip, much faster.

    #checkRunExist = os.popen("unzip -l $resultsFolder/output.zip | grep $eudatFolderName/run.sh" ).read()# Checks does zip contains run.sh file
    #if (not eudatFolderName + "/run.sh" in checkRunExist ):
    #log("Error: Folder does not contain run.sh file or client does not run ipfs daemon on the background.")
    #return; #detects error on the SLURM side.

   os.system("unzip -j $resultsFolder/output.zip -d $resultsFolder/JOB_TO_RUN");
   os.system("rm -f $resultsFolder/output.zip");
   
   isTarExist = os.popen("ls $resultsFolder/JOB_TO_RUN/*.tar.gz | wc -l").read();
   if int(isTarExist) > 0:
      os.popen("tar -xf $resultsFolder/JOB_TO_RUN/*.tar.gz -C $resultsFolder/JOB_TO_RUN" ).read();
      os.popen("rm -f $resultsFolder/JOB_TO_RUN/*.tar.gz").read();

   os.chdir(resultsFolder + '/JOB_TO_RUN'); # 'cd' into the working path and call sbatch from there
   sbatchCall();
#}

def driverIpfsCall(jobKey, index, folderType, miniLockId): #{
    global jobKeyGlobal; jobKeyGlobal=jobKey
    global indexGlobal;  indexGlobal=index;

    isIpfsOn();
    os.environ['jobKey']      = jobKey;
    os.environ['index']       = str(index);
    os.environ['ipfsHashes']  = str(ipfsHashes);
    os.environ['folderIndex'] = str(folderType);
    os.environ['shareToken']  = "-1";
    
    header = "var eBlocBroker = require('" + constants.EBLOCPATH + "/eBlocBrokerHeader.js')"; os.environ['header'] = header;

    if folderType == '0':
       os.environ['miniLockId'] = "-1"
    else:
       os.environ['miniLockId'] = miniLockId
       
    log("jobKey: " + jobKey);

    resultsFolder = ipfsHashes + '/' + jobKey + "_" + index;

    if not os.path.isdir(resultsFolder): # If folder does not exist
       os.system("mkdir -p " + resultsFolder);
       os.system("mkdir -p " + resultsFolder + '/JOB_TO_RUN');

    os.chdir(resultsFolder + '/JOB_TO_RUN');
    
    if os.path.isfile(jobKey):
       os.system('rm -f $jobKey');    

    ipfsCallCounter = 0;
    isIPFSHashExist = os.popen("bash $eblocPath/ipfsStat.sh $jobKey").read();

    log(isIPFSHashExist);
    
    os.environ['resultsFolder'] = resultsFolder + '/JOB_TO_RUN';
    if "CumulativeSize" in isIPFSHashExist:
       os.system('bash $eblocPath/ipfsGet.sh $jobKey $resultsFolder');

       if folderType == '2': # case for the ipfsMiniLock
          os.environ['passW'] = 'exfoliation econometrics revivifying obsessions transverse salving dishes';
          res = os.popen('mlck decrypt -f $resultsFolder/$jobKey --passphrase="$passW" --output-file=$resultsFolder/output.tar.gz').read();
          log(res)

          os.system('rm -f $resultsFolder/$jobKey');
          os.system('tar -xf $resultsFolder/output.tar.gz && rm -f $resultsFolder/output.tar.gz');

       if not os.path.isfile('run.sh'):
          log("run.sh does not exist")
          return
    else:
       log("!!!!!!!!!!!!!!!!!!!!!!! Markle not found! timeout for ipfs object stat retrieve !!!!!!!!!!!!!!!!!!!!!!!"); # IPFS file could not be accessed
       return;
    
    sbatchCall();
#}

# To test driverFunc.py executed as script.
if __name__ == '__main__': #{
   #var        = "3d8e2dc2-b855-1036-807f-9dbd8c6b1579=QmVvHrWzVmK3VASrGax7czDwfavwjgXgGmoeYRJtU6Az99";
   #index      = "0";
   #driverEudatCall(var, index);
   #------
   var        = "QmefdYEriRiSbeVqGvLx15DKh4WqSMVL8nT4BwvsgVZ7a5"
   index      = "1"
   myType     = "0"
   miniLockId = ""
   driverIpfsCall(var, index, myType, miniLockId);
#}

   '''
   while(True):
      if not(jobCoreNum == "notconnected" or jobCoreNum == ""):
         break;
      else:
         log("Error: Please run Parity or Geth on the background.**************************************************************")
         jobInfo    = os.popen('$contractCallPath/getJobInfo.py $clusterID $jobKey $index 2>/dev/null').read().rstrip('\n').replace(" ", "")[1:-1];
         jobInfo    = jobInfo.split(',');
         jobCoreNum = jobInfo[1];
   '''
   
