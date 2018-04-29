#!/usr/bin/env python

from datetime import datetime, timedelta
import owncloud, hashlib, getpass, sys, os, time, subprocess, constants, endCode
from   subprocess import call
import os.path
from colored import stylize
from colored import fg
import subprocess

jobKeyGlobal = "";
indexGlobal  = "";

# Paths==================================================
contractCallPath = constants.EBLOCPATH + '/contractCalls';
ipfsHashes       = constants.PROGRAM_PATH;
# ========================================================
os.environ['contractCallPath'] = contractCallPath;
os.environ['eblocPath']        = constants.EBLOCPATH;
os.environ['clusterID']        = constants.CLUSTER_ID

def log(strIn, color=''): #{
   if color != '':
      print(stylize(strIn, fg(color)));
   else:
      print(strIn)
   
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
            log("Error: Please run Parity or Geth on the background.", 'red')
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

def sbatchCall(): #{
   myDate = os.popen('LANG=en_us_88591 && date --date=\'1 seconds\' +"%b %d %k:%M:%S %Y"' ).read().rstrip('\n');
   log(myDate);
   txFile = open('../modifiedDate.txt', 'w');
   txFile.write(myDate + '\n' );   
   txFile.close();
   time.sleep(0.25);

   os.system("cp run.sh ${jobKey}*${index}*${folderIndex}*$shareToken.sh");
   
   jobInfo = os.popen('$contractCallPath/getJobInfo.py $clusterID $jobKey $index 2>/dev/null').read().rstrip('\n').replace(" ","")[1:-1];         
   jobInfo = jobInfo.split(',');

   jobCoreNum    = jobInfo[1];
   coreSecondGas = timedelta(seconds=int(int(jobInfo[5]) * 60)); # Client's requested seconds to run his/her job
   d             = datetime(1,1,1) + coreSecondGas;
   timeLimit     = str(int(d.day)-1) + '-' + str(d.hour) + ':' + str(d.minute); os.environ['timeLimit'] = timeLimit;   

   os.environ['jobCoreNum'] = jobCoreNum;
   log("timeLimit: " + str(timeLimit) + "| RequestedCoreNum: " + str(jobCoreNum)); 

   # SLURM submit job
   jobId = os.popen('sbatch -N$jobCoreNum $resultsFolder/${jobKey}*${index}*${folderIndex}*$shareToken.sh --mail-type=ALL | cut -d " " -f4-').read().rstrip('\n');
   os.environ['jobId'] = jobId;  
   os.popen('scontrol update jobid=$jobId TimeLimit=$timeLimit');
   
   if not jobId.isdigit():
      log("Error occured, jobId is not a digit.", 'red')
      return(); # Detects an error on the SLURM side
#}

def driverGdriveCall(jobKey, index, folderType): #{
   global jobKeyGlobal; jobKeyGlobal = jobKey
   global indexGlobal;  indexGlobal  = index;

   log("key: "   + jobKey);
   log("index: " + index);

   os.environ['jobKey']          = str(jobKey)
   os.environ['index']           = str(index);
   os.environ['folderIndex']     = folderType; 
   os.environ['shareToken']      = "-1";
   os.environ['GDRIVE_METADATA'] = constants.GDRIVE_METADATA;

   resultsFolderPrev = constants.PROGRAM_PATH + "/" + jobKey + "_" + index;
   resultsFolder     = constants.PROGRAM_PATH + "/" + jobKey + "_" + index + '/JOB_TO_RUN';
   os.environ['resultsFolderPrev'] = resultsFolderPrev;
   os.environ['resultsFolder']     = resultsFolder;
   
   if not os.path.isdir(constants.PROGRAM_PATH + "/" + jobKey + "_" + index): # If folder does not exist
      os.makedirs(constants.PROGRAM_PATH + "/" + jobKey + "_" + index)
      
   mimeType   = os.popen('gdrive info $jobKey -c $GDRIVE_METADATA | grep \'Mime\' | awk \'{print $2}\'').read().rstrip('\n')
   folderName = os.popen('gdrive info $jobKey -c $GDRIVE_METADATA | grep \'Name\' | awk \'{print $2}\'').read().rstrip('\n');
   os.environ['folderName']  = folderName;
   log(mimeType);
   
   if 'folder' in mimeType: #{ # Recieved job is in folder format
      log(os.popen("gdrive download --recursive $jobKey --force --path $resultsFolderPrev/").read()); # Gets the source code

      if not os.path.isdir(resultsFolderPrev + '/' + folderName): # Check before mv operation.
         log('Folder is not downloaded successfully.', 'red');
         sys.exit();
      
      os.system("mv $resultsFolderPrev/$folderName $resultsFolder");

      isTarExist = os.popen("ls -1 $resultsFolder/*.tar.gz 2>/dev/null | wc -l").read();
      if int(isTarExist) > 0:         
         log(os.popen("tar -xf $resultsFolder/*.tar.gz -C $resultsFolder" ).read());
         # os.popen("rm -f $resultsFolder/*.tar.gz").read(); # May delete anyother file ending with .tar.gz.

      isZipExist = os.popen("ls -1 $resultsFolder/*.zip 2>/dev/null | wc -l").read();
      if int(isZipExist) > 0:
         os.popen("unzip -j $resultsFolder/*.zip -d $resultsFolder").read();
         # os.popen("rm -f $resultsFolder/*.zip").read(); # May delete anyother file ending with .tar.gz.
   #}       
   elif 'gzip' in mimeType: # Recieved job is in folder tar.gz
      os.system("mkdir -p $resultsFolder"); # Gets the source code
      os.system("gdrive download $jobKey --force --path $resultsFolder/../"); # Gets the source code
      log(os.popen("tar -xf $resultsFolderPrev/*.tar.gz -C $resultsFolder" ).read());
      os.popen("rm -f $resultsFolderPrev/*.tar.gz").read();      
   elif 'zip' in mimeType: # Recieved job is in zip format
      os.system("mkdir -p $resultsFolder"); # Gets the source code
      os.system("gdrive download $jobKey --force --path $resultsFolderPrev/"); # Gets the source code
      log(os.popen('echo gdrive download --recursive $jobKey --force --path $resultsFolderPrev/').read())
      os.system("unzip -j $resultsFolderPrev/$folderName -d $resultsFolder");
      os.system("rm -f $resultsFolderPrev/$folderName");      
   else:
      sys.exit();

   if os.path.isdir(resultsFolder): # Check before mv operation.
      os.chdir(resultsFolder);      # 'cd' into the working path and call sbatch from there
      sbatchCall();    
#}

def driverGithubCall(jobKey, index, folderType): #{
   global jobKeyGlobal; jobKeyGlobal = jobKey
   global indexGlobal;  indexGlobal  = index;

   log("key: "   + jobKey);
   log("index: " + index)

   os.environ['jobKeyGit']   = str(jobKey).replace("=", "/")
   os.environ['index']       = str(index);
   os.environ['folderIndex'] = folderType; 
   os.environ['shareToken']  = "-1";

   resultsFolder = constants.PROGRAM_PATH + "/" + jobKey + "_" + index + '/JOB_TO_RUN'; 
   os.environ['resultsFolder'] = resultsFolder;

   if not os.path.isdir(constants.PROGRAM_PATH + "/" + jobKey + "_" + index): # If folder does not exist
      os.makedirs(constants.PROGRAM_PATH + "/" + jobKey + "_" + index)
 
   os.system("git clone https://github.com/$jobKeyGit.git $resultsFolder"); # Gets the source code
   os.chdir(resultsFolder); # 'cd' into the working path and call sbatch from there
   sbatchCall(); 
#}

def driverEudatCall(jobKey, index, fID): #{
   global jobKeyGlobal; jobKeyGlobal = jobKey
   global indexGlobal;  indexGlobal  = index;

   log("key: "   + jobKey);
   log("index: " + index);

   os.environ['jobKey']      = str(jobKey);
   os.environ['index']       = str(index);
   os.environ['folderIndex'] = "1";

   resultsFolder = constants.PROGRAM_PATH + "/" + jobKey + "_" + index + '/JOB_TO_RUN';
   os.environ['resultsFolderPrev'] = constants.PROGRAM_PATH + "/" + jobKey + "_" + index;
   os.environ['resultsFolder'] = resultsFolder;
   
   header = "var eBlocBroker = require('" + constants.EBLOCPATH + "/eBlocBrokerHeader.js')"; os.environ['header'] = header;
   f      = open(constants.EBLOCPATH + '/eudatPassword.txt', 'r') # Password is read from the file. password.txt is have only user access
   password = f.read().rstrip('\n').replace(" ", "");
   f.close()

   log("Login into owncloud" );
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

      if (inputFolderName == jobKey) and (inputOwner == fID):
         log("InputId:_" + inputId + "_ShareToken:_" + shareToken)
         os.environ['shareToken']      = str(shareToken);
         os.environ['eudatFolderName'] = str(inputFolderName);
         eudatFolderName               = inputFolderName;
         acceptFlag = 1;
         break;

   if acceptFlag == 0:
      oc.logout();
      log("Couldn't find the shared file", 'red');
      return;

   if not os.path.isdir(constants.PROGRAM_PATH + "/" + jobKey + "_" + index): # If folder does not exist
      os.makedirs(constants.PROGRAM_PATH + "/" + jobKey + "_" + index)
      
   #checkRunExist = os.popen("unzip -l $resultsFolder/output.zip | grep $eudatFolderName/run.sh" ).read()# Checks does zip contains run.sh file
   #if (not eudatFolderName + "/run.sh" in checkRunExist ):
   #log("Error: Folder does not contain run.sh file or client does not run ipfs daemon on the background.")
   #return; #detects error on the SLURM side.

   os.popen("wget https://b2drop.eudat.eu/s/$shareToken/download --output-document=$resultsFolderPrev/output.zip").read() # Downloads shared file as .zip, much faster.

   os.system("unzip -jo $resultsFolderPrev/output.zip -d $resultsFolder");
   os.system("rm -f $resultsFolderPrev/output.zip");

   isTarExist = os.popen("ls -1 $resultsFolder/*.tar.gz 2>/dev/null | wc -l").read();
   if int(isTarExist) > 0:
      os.popen("bash $eblocPath/tar.sh $resultsFolder" ).read(); # Extracting all *.tar.gz files.
      # os.popen("#!/bin/bash for a in $resultsFolder/*.tar.gz; do if [[ \"$a\" != result-* ]] ; then tar -xf \"$a\" -C $resultsFolder; fi done" ).read(); # Extracting all *.tar.gz files.
      # os.popen("rm -f $resultsFolder/*.tar.gz").read(); #uncomment

   isZipExist = os.popen("ls -1 $resultsFolder/*.zip 2>/dev/null | wc -l").read();
   if int(isTarExist) > 0:
      log(os.popen("" ).read());
      os.popen("unzip -jo $resultsFolderPrev/$jobKey -d $resultsFolder").read();
      os.popen("rm -f $resultsFolder/*.zip").read();

   os.chdir(resultsFolder); # 'cd' into the working path and call sbatch from there
   sbatchCall();
#}

def driverIpfsCall(jobKey, index, folderType): #{
    global jobKeyGlobal; jobKeyGlobal = jobKey
    global indexGlobal;  indexGlobal  = index;

    constants.isIpfsOn(os, time);
    os.environ['jobKey']      = jobKey;
    os.environ['index']       = str(index);
    os.environ['folderIndex'] = str(folderType);
    os.environ['shareToken']  = "-1";

    resultsFolder = constants.PROGRAM_PATH + "/" + jobKey + "_" + index + '/JOB_TO_RUN'; 
    os.environ['resultsFolder'] = resultsFolder;

    header = "var eBlocBroker = require('" + constants.EBLOCPATH + "/eBlocBrokerHeader.js')"; os.environ['header'] = header;
       
    log("jobKey: " + jobKey);

    if not os.path.isdir(constants.PROGRAM_PATH + "/" + jobKey + "_" + index): # If folder does not exist
       os.makedirs(constants.PROGRAM_PATH + "/" + jobKey + "_" + index)   
       os.system("mkdir -p " + resultsFolder);

    os.chdir(resultsFolder); # 'cd' into the working path and call sbatch from there
    
    if os.path.isfile(jobKey):
       os.system('rm -f $jobKey');    

    ipfsCallCounter = 0;
    isIPFSHashExist = os.popen("bash $eblocPath/ipfsStat.sh $jobKey").read();

    log(isIPFSHashExist);
    
    if "CumulativeSize" in isIPFSHashExist:
       os.system('bash $eblocPath/ipfsGet.sh $jobKey $resultsFolder');

       if folderType == '2': # case for the ipfsMiniLock
          os.environ['passW'] = 'bright wind east is pen be lazy usual';
          log(os.popen('mlck decrypt -f $resultsFolder/$jobKey --passphrase="$passW" --output-file=$resultsFolder/output.tar.gz').read());

          os.system('rm -f $resultsFolder/$jobKey');
          os.system('tar -xf $resultsFolder/output.tar.gz && rm -f $resultsFolder/output.tar.gz');

       if not os.path.isfile('run.sh'):
          log("run.sh does not exist", 'red')
          return
    else:
       log("!!!!!!!!!!!!!!!!!!!!!!! Markle not found! timeout for ipfs object stat retrieve !!!!!!!!!!!!!!!!!!!!!!!", 'red'); # IPFS file could not be accessed
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

   driverIpfsCall(var, index, myType);
#}
