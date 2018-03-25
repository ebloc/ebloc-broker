#!/usr/bin/env python

import owncloud, hashlib, getpass, sys, os, time, subprocess, constants, endCode
from subprocess import call

# Paths---------
eblocPath        = constants.EBLOCPATH;
contractCallPath = constants.EBLOCPATH + '/contractCalls'; os.environ['contractCallPath'] = contractCallPath;
ipfsHashes       = constants.PROGRAM_PATH
# ---------------
jobKeyGlobal = "";
indexGlobal  = "";

def logTest(strIn):
   print(strIn)
   txFile = open(constants.LOG_PATH + '/transactions/' + jobKeyGlobal + '_' + indexGlobal + '_driverOutput' +'.txt', 'a');
   txFile.write(strIn + "\n");
   txFile.close();

   # If non-thread tests are running
   txFile = open(constants.LOG_PATH + '/transactions/clusterOut.txt', 'a');
   txFile.write(strIn + "\n");
   txFile.close();

def contractCall(val):
   printFlag=1;
   ret = os.popen(val + "| node").read().rstrip('\n').replace(" ", "");
   while(True):
      if (not(ret == "notconnected" or ret == "")):
         break;
      else:
         if (printFlag == 1):
            logTest("Error: Please run Parity or Geth on the background.**************************************************************")
            printFlag = 0;
            ret = os.popen(val + "| node").read().rstrip('\n').replace(" ", "");
            time.sleep(1);
   return ret;

# checks: does SLURM run on the background or not
def isSlurmOn(): 
   os.environ['logPath'] = constants.LOG_PATH;
   os.system("bash checkSinfo.sh")  
   check = os.popen("cat $logPath/checkSinfoOut.txt").read()

   if (not "PARTITION" in str(check)) or ("sinfo: error" in str(check)):
      print('slurm is not on.')
      os.system("sudo bash runSlurm.sh");

# checks: does IPFS run on the background or not
def isIpfsOn():
   check = os.popen("ps aux | grep \'[i]pfs daemon\' | wc -l").read().rstrip('\n');
   if (int(check) == 0):
      logTest( "Error: IPFS does not work on the background. Please do:\nipfs daemon & " )
      sys.exit()

def driverEudatCall(jobKey, index):
   global jobKeyGlobal; jobKeyGlobal=jobKey
   global indexGlobal;  indexGlobal=index;

   logTest("key: "   + jobKey)
   logTest("index: " + index)

   os.environ['jobKey']      = str(jobKey)
   os.environ['index']       = str(index);
   os.environ['clusterID']   = constants.CLUSTER_ID
   os.environ['eblocPath']   = eblocPath
   os.environ['folderIndex'] = "1";
   os.environ['miniLockId']  = "-1";
   os.environ['whoami']      = constants.WHOAMI
   whoami                    = os.system("whoami")# To learn running as root or userName

   jobKeyTemp = jobKey.split('=');
   owner      = jobKeyTemp[0]
   folderName = jobKeyTemp[1]
   header     = "var eBlocBroker = require('" + eblocPath + "/eBlocBrokerHeader.js')"; os.environ['header']     = header;

   f        = open(eblocPath + '/eudatPassword.txt', 'r') # Password is read from the file. password.txt is have only user access
   password = f.read().rstrip('\n').replace(" ", ""); f.close()

   logTest("Login into owncloud")
   oc = owncloud.Client('https://b2drop.eudat.eu/')
   oc.login('aalimog1@binghamton.edu', password ); # Unlocks EUDAT account
   shareList = oc.list_open_remote_share();

   logTest("finding_acceptId")
   acceptFlag = 0;
   eudatFolderName = ""
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

   localOwnCloudPathFolder = ipfsHashes + '/' + jobKey + "_" + index; os.environ['localOwnCloudPathFolder'] = localOwnCloudPathFolder

   if not os.path.isdir(localOwnCloudPathFolder): # If folder does not exist
      os.makedirs(localOwnCloudPathFolder)

   os.popen("wget https://b2drop.eudat.eu/s/$shareToken/download --output-document=$localOwnCloudPathFolder/output.zip" ).read()# Downloads shared file as zip

    #run.tar.gz check yap.    
    #checkRunExist = os.popen("unzip -l $localOwnCloudPathFolder/output.zip | grep $eudatFolderName/run.sh" ).read()# Checks does zip contains run.sh file
    #if (not eudatFolderName + "/run.sh" in checkRunExist ):
    #logTest("Error: Folder does not contain run.sh file or client does not run ipfs daemon on the background.")
    #return; #detects error on the SLURM side.

   os.popen("unzip $localOwnCloudPathFolder/output.zip -d      $localOwnCloudPathFolder/.").read()
   os.popen("mv    $localOwnCloudPathFolder/$eudatFolderName/* $localOwnCloudPathFolder/ ").read()
   os.popen("rm    $localOwnCloudPathFolder/output.zip"                                   )
   os.popen("rmdir $localOwnCloudPathFolder/$eudatFolderName"                             )
   myDate = os.popen('LANG=en_us_88591 && date +"%b %d %k:%M:%S:%N %Y"' ).read().rstrip('\n'); #logTest(myDate);
   txFile = open(localOwnCloudPathFolder + '/modifiedDate.txt', 'w'); txFile.write(myDate + '\n'); txFile.close();
   time.sleep(0.2)

   isTarExist = os.popen("ls $localOwnCloudPathFolder/*.tar.gz | wc -l").read();
   if int(isTarExist) > 0:
      os.popen("tar -xf $localOwnCloudPathFolder/*.tar.gz -C $localOwnCloudPathFolder/" ).read();
      os.popen("rm $localOwnCloudPathFolder/*.tar.gz").read();
      
   os.system("cp $localOwnCloudPathFolder/run.sh $localOwnCloudPathFolder/${jobKey}_${index}_${folderIndex}_${shareToken}_$miniLockId.sh");

   logTest("localOwnCloudPathFolder: " + localOwnCloudPathFolder)

   jobInfo    = os.popen('python $contractCallPath/getJobInfo.py $clusterID $jobKey $index').read().rstrip('\n').replace(" ", "")[1:-1];
   jobInfo    = jobInfo.split(',');
   jobCoreNum = jobInfo[1];

   while(True):
      if not(jobCoreNum == "notconnected" or jobCoreNum == ""):
         break;
      else:
         logTest("Error: Please run Parity or Geth on the background.**************************************************************")
         jobInfo    = os.popen('python $contractCallPath/getJobInfo.py $clusterID $jobKey $index').read().rstrip('\n').replace(" ", "")[1:-1];
         jobInfo    = jobInfo.split(',');
         jobCoreNum = jobInfo[1]

   os.environ['jobCoreNum'] = jobCoreNum;
   logTest("Job's Core Number: " + jobCoreNum)

   isSlurmOn();

   os.chdir(localOwnCloudPathFolder) # 'cd' into the working path and call sbatch from there
   if whoami == "root":
      jobId = os.popen('sbatch -U root -N$jobCoreNum $localOwnCloudPathFolder/${jobKey}_${index}_${folderIndex}_${shareToken}_$miniLockId.sh --mail-type=ALL | cut -d " " -f4-').read().rstrip('\n');
   else:
      jobId = os.popen('sbatch         -N$jobCoreNum $localOwnCloudPathFolder/${jobKey}_${index}_${folderIndex}_${shareToken}_$miniLockId.sh --mail-type=ALL | cut -d " " -f4-').read().rstrip('\n');
      os.environ['jobId'] = jobId;
      logTest("jobId: "+ str(jobId));

   oc.logout();
   if not jobId.isdigit(): #{
      # Detected an error on the SLURM side      
      logTest("Error occured, jobId is not a digit.");
      return();
   #}
   
def driverIpfsCall(ipfsHash, index, ipfsType, miniLockId):
    global jobKeyGlobal; jobKeyGlobal=ipfsHash
    global indexGlobal;  indexGlobal=index;

    os.environ['ipfsHash']    = ipfsHash;
    os.environ['index']       = str(index);
    os.environ['clusterID']   = constants.CLUSTER_ID
    os.environ['ipfsHashes']  = str(ipfsHashes);
    os.environ['folderIndex'] = str(ipfsType);
    os.environ['eblocPath']   = eblocPath
    os.environ['shareToken']  = "-1"
    os.environ['whoami']      = constants.WHOAMI
    whoami                    = os.system("whoami" )

    if (ipfsType == '0'):
       os.environ['miniLockId'] = "-1"
    else:
       os.environ['miniLockId'] = miniLockId

    header = "var eBlocBroker = require('" + eblocPath + "/eBlocBrokerHeader.js')"; os.environ['header'] = header;
    logTest("ipfsHash: " + ipfsHash);

    jobSavePath = ipfsHashes + '/' + ipfsHash + "_" + index;
    os.environ['jobSavePath']   = jobSavePath

    if not os.path.isdir(jobSavePath): # If folder does not exist
       os.environ['mkdirPath'] = jobSavePath;
       if (whoami == "root"):
          os.system("sudo -u $whoami mkdir $mkdirPath");
       else:
          os.system("                mkdir $mkdirPath");

    os.chdir(jobSavePath)
    if os.path.isfile(ipfsHash):
       os.system('rm $ipfsHash');

    ipfsCallCounter=0;

    isIPFSHashExist=""
    if (whoami == "root"):
       isIPFSHashExist = os.popen("sudo -u $whoami bash $eblocPath/ipfsStat.sh $ipfsHash").read();
    else:
       isIPFSHashExist = os.popen("                bash $eblocPath/ipfsStat.sh $ipfsHash").read();

    logTest(isIPFSHashExist);

    if (constants.IPFS_USE == 1):
          isIpfsOn();

    if ("CumulativeSize" in isIPFSHashExist):
       if (whoami == "root"):
          os.system('sudo -u $whoami bash $eblocPath/ipfsGet.sh $ipfsHash $jobSavePath');
       else:
          os.system('                bash $eblocPath/ipfsGet.sh $ipfsHash $jobSavePath');

       if (ipfsType == '2'): # case for the ipfsMiniLock
          os.environ['passW'] = 'exfoliation econometrics revivifying obsessions transverse salving dishes';
          res = os.popen('mlck decrypt -f $jobSavePath/$ipfsHash --passphrase="$passW" --output-file=$jobSavePath/output.tar.gz').read();
          logTest(res)

          os.system('rm $jobSavePath/$ipfsHash');
          os.system('tar -xf $jobSavePath/output.tar.gz && rm $jobSavePath/output.tar.gz');

       if not os.path.isfile('run.sh'):
          logTest("Run.sh does not exist")
          return
    else:
       logTest("Markle not found! timeout for ipfs object stat retrieve ! <========="); # IPFS file could not be accessed
       return;

    myDate = os.popen('LANG=en_us_88591 && date +"%b %d %k:%M:%S:%N %Y"' ).read().rstrip('\n'); logTest(myDate);
    txFile = open('modifiedDate.txt', 'w'); txFile.write(myDate + '\n' ); txFile.close();
    time.sleep(0.2)

    os.system("cp run.sh ${ipfsHash}_${index}_${folderIndex}_${shareToken}_$miniLockId.sh");

    jobInfo = os.popen('python $contractCallPath/getJobInfo.py $clusterID $ipfsHash $index').read().rstrip('\n').replace(" ","")[1:-1];         
    jobInfo = jobInfo.split(',');
    jobCoreNum = jobInfo[1]

    os.environ['jobCoreNum'] = jobCoreNum;
    logTest("RequestedCoreNum: " + str(jobCoreNum))

    # SLURM submit job
    if (whoami == "root"):
       jobId = os.popen('sbatch -U root -N$jobCoreNum $ipfsHashes/${ipfsHash}_$index/${ipfsHash}_${index}_${folderIndex}_${shareToken}_$miniLockId.sh --mail-type=ALL | cut -d " " -f4-').read().rstrip('\n');
    else:
       jobId = os.popen('sbatch         -N$jobCoreNum $ipfsHashes/${ipfsHash}_$index/${ipfsHash}_${index}_${folderIndex}_${shareToken}_$miniLockId.sh --mail-type=ALL | cut -d " " -f4-').read().rstrip('\n');

    os.environ['jobId'] = jobId;
    if not jobId.isdigit():
       logTest("Error occured, jobId is not a digit.")
       return(); # Detects na error on the SLURM side

    if (whoami == "root"):
       os.popen("sudo chown $whoami: $jobSavePath")

# To test driverFunc.py executed as script.
if __name__ == '__main__': #{
   #var        = "3d8e2dc2-b855-1036-807f-9dbd8c6b1579=QmVvHrWzVmK3VASrGax7czDwfavwjgXgGmoeYRJtU6Az99";
   #index      = "0";
   #driverEudatCall(var, index);
   #------
   var    = "QmefdYEriRiSbeVqGvLx15DKh4WqSMVL8nT4BwvsgVZ7a5"
   index  = "1"
   myType = "0"
   miniLockId = ""

   driverIpfsCall(var, index, myType, miniLockId);
#}
