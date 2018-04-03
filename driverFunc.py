#!/usr/bin/env python

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

def logTest(strIn): #{
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
            logTest("Error: Please run Parity or Geth on the background.**************************************************************")
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
      logTest("Error: IPFS does not work on the background. Running:\nipfs daemon &");
      os.system("bash " + constants.EBLOCPATH + "/runIPFS.sh");
      time.sleep(5);
      os.system("cat ipfs.out");
   else:
      logTest("IPFS is already on");
#}

def sbatchCall(): #{
   myDate = os.popen('LANG=en_us_88591 && date +"%b %d %k:%M:%S:%N %Y"' ).read().rstrip('\n'); logTest(myDate);
   txFile = open('modifiedDate.txt', 'w'); txFile.write(myDate + '\n' );
   txFile.close();
   time.sleep(0.25)

   os.system("cp run.sh ${jobKey}_${index}_${folderIndex}_${shareToken}_$miniLockId.sh");
   jobInfo = os.popen('python $contractCallPath/getJobInfo.py $clusterID $jobKey $index').read().rstrip('\n').replace(" ","")[1:-1];         
   jobInfo = jobInfo.split(',');
   jobCoreNum = jobInfo[1]

   os.environ['jobCoreNum'] = jobCoreNum;
   logTest("RequestedCoreNum: " + str(jobCoreNum))

   # SLURM submit job
   jobId = os.popen('sbatch -N$jobCoreNum $ipfsHashes/${jobKey}_$index/${jobKey}_${index}_${folderIndex}_${shareToken}_$miniLockId.sh --mail-type=ALL | cut -d " " -f4-').read().rstrip('\n');

   os.environ['jobId'] = jobId;
   if not jobId.isdigit():
      logTest("Error occured, jobId is not a digit.")
      return(); # Detects an error on the SLURM side
#}

#------------------------------------------------------------------------------
      
def driverGithubCall(jobKey, index):
   global jobKeyGlobal; jobKeyGlobal = jobKey
   global indexGlobal;  indexGlobal  = index;

   logTest("key: "   + jobKey);
   logTest("index: " + index)

   os.environ['jobKey']      = str(jobKey)
   os.environ['jobKeyGit']   = str(jobKey).replace("=", "/")
   os.environ['index']       = str(index);

   os.environ['ipfsHashes']  = str(ipfsHashes);
   os.environ['folderIndex'] = "3"; 
   os.environ['shareToken']  = "-1";
   os.environ['miniLockId']  = "-1";

   localOwnCloudPathFolder = ipfsHashes + '/' + jobKey + "_" + index; os.environ['localOwnCloudPathFolder'] = localOwnCloudPathFolder;
   
   if not os.path.isdir(localOwnCloudPathFolder): # If folder does not exist
      os.makedirs(localOwnCloudPathFolder)
 
   os.popen("git clone https://github.com/$jobKeyGit.git $localOwnCloudPathFolder/"); # Gets the source code
   os.chdir(localOwnCloudPathFolder);   
   sbatchCall(); 
   
def driverEudatCall(jobKey, index):
   global jobKeyGlobal; jobKeyGlobal = jobKey
   global indexGlobal;  indexGlobal  = index;

   logTest("key: "   + jobKey)
   logTest("index: " + index)

   os.environ['jobKey']      = str(jobKey);
   os.environ['index']       = str(index);
   os.environ['ipfsHashes']  = str(ipfsHashes);
   os.environ['folderIndex'] = "1";
   os.environ['miniLockId']  = "-1";

   jobKeyTemp = jobKey.split('=');
   owner      = jobKeyTemp[0]
   folderName = jobKeyTemp[1]
   header     = "var eBlocBroker = require('" + constants.EBLOCPATH + "/eBlocBrokerHeader.js')"; os.environ['header']     = header;

   f        = open(constants.EBLOCPATH + '/eudatPassword.txt', 'r') # Password is read from the file. password.txt is have only user access
   password = f.read().rstrip('\n').replace(" ", ""); f.close()

   logTest("Login into owncloud");
   oc = owncloud.Client('https://b2drop.eudat.eu/');
   oc.login('aalimog1@binghamton.edu', password); # Unlocks EUDAT account
   shareList = oc.list_open_remote_share();

   logTest("finding_acceptId")
   acceptFlag      = 0;
   eudatFolderName = "";
   for i in range(len(shareList)-1, -1, -1): # Starts iterating from last item  to first one
      inputFolderName = shareList[i]['name']
      inputFolderName = inputFolderName[1:] # Removes '/' on the beginning
      inputId         = shareList[i]['id']
      inputOwner      = shareList[i]['owner']
      shareToken      = shareList[i]['share_token']

      if (inputFolderName == folderName) and (inputOwner == owner):
         logTest("InputId:_" + inputId + "_ShareToken:_" + shareToken)
         os.environ['shareToken']      = str(shareToken);
         os.environ['eudatFolderName'] = str(inputFolderName);
         eudatFolderName               = inputFolderName;
         acceptFlag = 1;
         break;

   if acceptFlag == 0:
      oc.logout()
      logTest("Couldn't find the shared file");
      return;

   localOwnCloudPathFolder = ipfsHashes + '/' + jobKey + "_" + index; os.environ['localOwnCloudPathFolder'] = localOwnCloudPathFolder;

   if not os.path.isdir(localOwnCloudPathFolder): # If folder does not exist
      os.makedirs(localOwnCloudPathFolder)

   os.popen("wget https://b2drop.eudat.eu/s/$shareToken/download --output-document=$localOwnCloudPathFolder/output.zip" ).read() # Downloads shared file as .zip.

    #checkRunExist = os.popen("unzip -l $localOwnCloudPathFolder/output.zip | grep $eudatFolderName/run.sh" ).read()# Checks does zip contains run.sh file
    #if (not eudatFolderName + "/run.sh" in checkRunExist ):
    #logTest("Error: Folder does not contain run.sh file or client does not run ipfs daemon on the background.")
    #return; #detects error on the SLURM side.

   os.popen("unzip $localOwnCloudPathFolder/output.zip -d      $localOwnCloudPathFolder/.").read();
   os.popen("mv    $localOwnCloudPathFolder/$eudatFolderName/* $localOwnCloudPathFolder/ ").read();
   os.popen("rm    $localOwnCloudPathFolder/output.zip"                                   );
   os.popen("rmdir $localOwnCloudPathFolder/$eudatFolderName"                             );
   
   isTarExist = os.popen("ls $localOwnCloudPathFolder/*.tar.gz | wc -l").read();
   if int(isTarExist) > 0:
      os.popen("tar -xf $localOwnCloudPathFolder/*.tar.gz -C $localOwnCloudPathFolder/" ).read();
      os.popen("rm $localOwnCloudPathFolder/*.tar.gz").read();
      
   os.chdir(localOwnCloudPathFolder); # 'cd' into the working path and call sbatch from there
   sbatchCall();
      
def driverIpfsCall(jobKey, index, folderType, miniLockId):
    global jobKeyGlobal; jobKeyGlobal=jobKey
    global indexGlobal;  indexGlobal=index;

    os.environ['jobKey']      = jobKey;
    os.environ['index']       = str(index);
    os.environ['ipfsHashes']  = str(ipfsHashes);
    os.environ['folderIndex'] = str(folderType);
    os.environ['shareToken']  = "-1"
    
    if folderType == '0':
       os.environ['miniLockId'] = "-1"
    else:
       os.environ['miniLockId'] = miniLockId

    header = "var eBlocBroker = require('" + constants.EBLOCPATH + "/eBlocBrokerHeader.js')";
    os.environ['header'] = header;
    logTest("jobKey: " + jobKey);

    jobSavePath = ipfsHashes + '/' + jobKey + "_" + index;
    os.environ['jobSavePath']   = jobSavePath

    if not os.path.isdir(jobSavePath): # If folder does not exist
       os.environ['mkdirPath'] = jobSavePath;
       os.system("mkdir $mkdirPath");

    os.chdir(jobSavePath)
    if os.path.isfile(jobKey):
       os.system('rm $jobKey');

    isIpfsOn();

    ipfsCallCounter = 0;
    isIPFSHashExist = os.popen("bash $eblocPath/ipfsStat.sh $jobKey").read();

    logTest(isIPFSHashExist);

    if ("CumulativeSize" in isIPFSHashExist):
       os.system('bash $eblocPath/ipfsGet.sh $jobKey $jobSavePath');

       if (folderType == '2'): # case for the ipfsMiniLock
          os.environ['passW'] = 'exfoliation econometrics revivifying obsessions transverse salving dishes';
          res = os.popen('mlck decrypt -f $jobSavePath/$jobKey --passphrase="$passW" --output-file=$jobSavePath/output.tar.gz').read();
          logTest(res)

          os.system('rm $jobSavePath/$jobKey');
          os.system('tar -xf $jobSavePath/output.tar.gz && rm $jobSavePath/output.tar.gz');

       if not os.path.isfile('run.sh'):
          logTest("Run.sh does not exist")
          return
    else:
       logTest("Markle not found! timeout for ipfs object stat retrieve ! <========="); # IPFS file could not be accessed
       return;
    
    sbatchCall();
   
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
         logTest("Error: Please run Parity or Geth on the background.**************************************************************")
         jobInfo    = os.popen('python $contractCallPath/getJobInfo.py $clusterID $jobKey $index').read().rstrip('\n').replace(" ", "")[1:-1];
         jobInfo    = jobInfo.split(',');
         jobCoreNum = jobInfo[1];
   '''
   
