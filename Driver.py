#!/usr/bin/env python

from subprocess import call
import sys, os, time, subprocess, string, driverFunc, constants, _thread
from colored import stylize
from colored import fg
import cancelJob

# p = subprocess.Popen([sys.executable, '-c', 'print (\'hello\'); cancelJob.cancelJob()'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT); print('finished')

# Paths================================================================
jobsReadFromPath               = constants.JOBS_READ_FROM_FILE;
os.environ['jobsReadFromPath'] = jobsReadFromPath
contractCallPath               = constants.EBLOCPATH + '/contractCalls';
os.environ['eblocPath']        = constants.EBLOCPATH;
os.environ['contractCallPath'] = contractCallPath;
os.environ['logPath']          = constants.LOG_PATH;
totalCore = os.popen('sinfo | awk \'{print $4}\' | tail -n +2').read().rstrip('\n');
# ======================================================================

#rows, columns = os.popen('stty size', 'r').read().split();
columns = 100;

def log(strIn, color=''): #{
   if color != '':
      print(stylize(strIn, fg(color)));
   else:
      print(strIn)
      
   txFile = open(constants.LOG_PATH + '/transactions/clusterOut.txt', 'a');
   txFile.write(strIn + "\n");
   txFile.close();   
#}

def slurmPendingJobCheck(): #{
    global totalCore;    
    printFlag = 0;
    usedCoreNum = os.popen('squeue | grep -P \' R      \' | awk \'{print $7}\' | paste -sd+ - | bc').read().rstrip('\n');

    if usedCoreNum == '':
       usedCoreNum = 0;

    # log('There is ' +  usedCoreNum + ' used core out of ' + totalCore + '.', 'green');    
    while True: #{
       if int(totalCore) - int(usedCoreNum) > 0:
          log('There is ' +  usedCoreNum + ' used core out of ' + totalCore + '.', 'green')       
          break;
       if printFlag == 0:
          log('Waiting running jobs to be completed.', 'blue')
          printFlag = 1;
       time.sleep(10);       
       usedCoreNum = os.popen('squeue | grep -P \' R      \' | awk \'{print $7}\' | paste -sd+ - | bc').read().rstrip('\n');
    #}     
#}

# checks: does Geth runs on the background
def isGethOn(): #{  
   check = os.popen("ps aux | grep [g]eth | grep " + str(constants.RPC_PORT) + "| wc -l").read().rstrip('\n');

   if int(check) == 0:
      log("Geth is not running on the background.", 'red');
      sys.exit();      
#}

# checks: does Driver.py runs on the background
def isDriverOn(): 
   check = os.popen("ps aux | grep \'[D]river.py\' | grep \'python\' | wc -l").read().rstrip('\n');

   if int(check) > 1:
      log("Driver is already running.", 'green');
      sys.exit();

# checks: does Slurm runs on the background or not
def isSlurmOn(): #{

   os.system("bash checkSinfo.sh")  
   check = os.popen("cat $logPath/checkSinfoOut.txt").read();

   if not "PARTITION" in str(check):
      log("Error: sinfo returns emprty string, please run:\nsudo bash runSlurm.sh\n", "red");      
      log('Error Message: \n' + check, "red");
      sys.exit();

   if "sinfo: error" in str(check):
      log("Error on munged: \n" + check)
      log("Please Do:\n")
      log("sudo munged -f")
      log("/etc/init.d/munge start")
      sys.exit()

   global totalCore;
   totalCore = os.popen('sinfo | awk \'{print $4}\' | tail -n +2 | paste -sd+ - | bc').read().rstrip('\n');
#}

yes = set(['yes', 'y', 'ye']);
no  = set(['no' , 'n']);

if constants.WHOAMI == '' or constants.EBLOCPATH == '' or constants.CLUSTER_ID == '':
   print(stylize('Once please run:  bash initialize.sh \n', fg('red')));
   sys.exit();

isDriverOn();
isSlurmOn();
isGethOn();
   
isContractExist = os.popen('$contractCallPath/isContractExist.py').read().rstrip('\n');
if 'False' in isContractExist:
   log('Please check that you are using eBloc blockchain.', 'red');
   sys.exit();

log('=' * int(int(columns) / 2  - 12)   + ' cluster session starts ' + '=' * int(int(columns) / 2 - 12), "green");
log('isWeb3Connected: ' + os.popen('$contractCallPath/isWeb3Connected.py').read().rstrip('\n'))
log('rootdir: ' + os.getcwd());

if constants.IPFS_USE == 1:
   constants.isIpfsOn(os, time);
   
header    = "var eBlocBroker = require('" + constants.EBLOCPATH + "/eBlocBrokerHeader.js')";
os.environ['header'] = header;

clusterID = constants.CLUSTER_ID;
os.environ['clusterID'] = clusterID;

isClusterExist = os.popen('$contractCallPath/isClusterExist.py $clusterID').read().rstrip('\n');

if "false" in isClusterExist.lower(): #{
   print(stylize("Error: Your Ethereum address '" + clusterID + "' \n"
                 "does not match with any cluster in eBlocBroker. Please register your \n" 
                 "cluster using your Ethereum Address in to the eBlocBroker. You can \n"   
                 "use 'contractCalls/registerCluster.py' script to register your cluster.", fg('red')));
   sys.exit()
#}

deployedBlockNumber = os.popen('$contractCallPath/getDeployedBlockNumber.py').read().rstrip('\n');
blockReadFromContract = str(0);

log('{0: <21}'.format('clusterAddress:') +  clusterID, "yellow")

if not os.path.isfile(constants.BLOCK_READ_FROM_FILE): #{
   f = open(constants.BLOCK_READ_FROM_FILE, 'w')
   f.write( deployedBlockNumber + "\n")
   f.close()
#}

f = open(constants.BLOCK_READ_FROM_FILE, 'r')
blockReadFromLocal = f.read().rstrip('\n');
f.close();

if not blockReadFromLocal.isdigit(): #{
   log("Error: constants.BLOCK_READ_FROM_FILE is empty or contains and invalid value")
   log("> Would you like to read from contract's deployed block number? y/n")   
   while True: #{
      choice = input().lower()
      if choice in yes:
         blockReadFromLocal = deployedBlockNumber;
         f = open(constants.BLOCK_READ_FROM_FILE, 'w')
         f.write( deployedBlockNumber + "\n")
         f.close()
         log("\n")
         break;
      elif choice in no:
         sys.exit()
      else:
         sys.stdout.write("Please respond with 'yes' or 'no'");
   #}
#}

blockReadFrom = 0;
if (int(blockReadFromLocal) < int(blockReadFromContract)):
   blockReadFrom = blockReadFromContract;
else:
   blockReadFrom = blockReadFromLocal;
             
clusterGainedAmountInit = os.popen('$contractCallPath/getClusterReceivedAmount.py $clusterID').read().rstrip('\n');

log('{0: <21}'.format('deployedBlockNumber:') +  deployedBlockNumber + "| Cluster's initial money: " + clusterGainedAmountInit)

os.system('rm -f $logPath/queuedJobs.txt && rm -f $jobsReadFromPath'); # Remove queuedJobs from previous test.
while True: #{    
    if "Error" in blockReadFrom:
       log(blockReadFrom);
       sys.exit();

    clusterGainedAmount = os.popen('$contractCallPath/getClusterReceivedAmount.py $clusterID').read().rstrip('\n');    
    squeueStatus        = os.popen("squeue").read();

    if "squeue: error:" in str(squeueStatus): #{
       log("SLURM is not running on the background, please run \'sudo bash runSlurm.sh\'. \n");
       log(squeueStatus);
       sys.exit();
    #}
    
    log("Current Slurm Running jobs status: \n" + squeueStatus);
    log('-' * int(columns), "green")
    if 'notconnected' != clusterGainedAmount:
       log("Current Time: " + time.ctime() + '| ClusterGainedAmount: ' + str(int(clusterGainedAmount) - int(clusterGainedAmountInit)));
    log("Waiting new job to come since block number: " + blockReadFrom);

    printFlag          = 0;
    passedPrintFlag    = 0;
    currentBlockNumber = os.popen('$contractCallPath/blockNumber.py').read().rstrip('\n');
    
    while True: #{
       if (printFlag == 0):
          log("Waiting new block to increment by one.");
          log("Current BlockNumber: " + currentBlockNumber  + "| sync from block number: " + blockReadFrom);
          
       if int(currentBlockNumber) >= int(blockReadFrom):
          break;
       
       printFlag = 1;
       time.sleep(2);
       currentBlockNumber = os.popen('$contractCallPath/blockNumber.py').read().rstrip('\n');

       if (passedPrintFlag == 0):
          log("Passed incremented block number... Continue to wait from block number: " + blockReadFrom);
          passedPrintFlag = 1;
    #}
    
    passedPrintFlag = 0;      
    os.environ['blockReadFrom'] = str(blockReadFrom) # Starting reading event's location has been updated

    slurmPendingJobCheck()
    
    constants.contractCall('eBlocBroker.LogJob($blockReadFrom, \'$jobsReadFromPath\')'); # Waits here until new job submitted into the cluster
    print('isWeb3Connected: ' + os.popen('$contractCallPath/isWeb3Connected.py').read().rstrip('\n'))
    if os.path.isfile(jobsReadFromPath): #{ Waits until generated file on log is completed       
       submittedJobs = set() # holds lines already seen
       for line in open(jobsReadFromPath, "r"):
          if line not in submittedJobs: # not a duplicate
             submittedJobs.add(line)

       submittedJobs= sorted(submittedJobs);
             
       maxVal               = 0;       
       isClusterReceivedJob = 0;       
       submittedJob         = 0;
       counter = 0;

       for e in submittedJobs: #{
          runFlag = 0;
          submittedJob = e.rstrip('\n').split(' ');          
          if clusterID == submittedJob[1]: # Only obtain jobs that are submitted to the cluster
             isClusterReceivedJob = 1;
             log(str(counter) + ' ' + '-' * (int(columns) - 2), "green");
             counter += 1;
             log("BlockNum: " + submittedJob[0].rstrip('\n') + " " + submittedJob[1] + " " + submittedJob[2] + " " + submittedJob[3] + " " + submittedJob[4]);

             if int(submittedJob[0]) > int(maxVal):
                maxVal = submittedJob[0]

             os.environ['jobKey'] = submittedJob[2];
             os.environ['index']  = submittedJob[3];

             strCheck = os.popen('bash $eblocPath/strCheck.sh $jobKey').read();
             
             jobInfo = os.popen('$contractCallPath/getJobInfo.py $clusterID $jobKey $index 2>/dev/null 2>/dev/null').read().rstrip('\n').replace(" ", "")[1:-1];

             if not ',' in jobInfo or jobInfo == '': #{
                log("jobInfo is returned as empty string. Geth might be closed", 'red');
                runFlag = 1;
             #}
             
             jobInfo = jobInfo.split(',');
             log('jobOwner/userID: ' +  jobInfo[6].replace("u'", "").replace("'", ""));             
             os.environ['userID'] = jobInfo[6].replace("u'", "").replace("'", "");
             
             isUserExist = os.popen('$contractCallPath/isUserExist.py $userID 2>/dev/null').read().rstrip('\n');
             
             userInfo = os.popen('$contractCallPath/getUserInfo.py $userID 1 2>/dev/null').read().rstrip('\n').replace(" ", "");
             userInfo = userInfo.split(',');            

             if jobInfo[0] == str(constants.job_state_code['COMPLETED']):
                log("Job is already completed.", 'red');
                runFlag = 1;
             if jobInfo[0] == str(constants.job_state_code['REFUNDED']):
                log("Job is refunded.", 'red');
                runFlag = 1;
             if runFlag == 0 and not jobInfo[0] == str(constants.job_state_code['PENDING']):
                log("Job is already captured and in process or completed.", 'red');
                runFlag = 1;
             if "false" in isUserExist.lower(): 
                log('jobOwner is not registered', 'red');
                runFlag = 1;
             if 'False' in strCheck:
                log('Filename contains invalid character', 'red');
                runFlag = 1;
                
             slurmPendingJobCheck()
             # Checks isAlreadyCaptured job or not. If it is completed job do not obtain it
             if runFlag == 1:
                pass;
             elif submittedJob[4] == '0':
                log("New job has been received. IPFS call |" + time.ctime(), "green")
                driverFunc.driverIpfsCall(submittedJob[2], submittedJob[3], submittedJob[4]); 
             elif submittedJob[4] == '1':
                log("New job has been received. EUDAT call |" + time.ctime(), "green");
                driverFunc.driverEudatCall(submittedJob[2], submittedJob[3], userInfo[4]);
                #thread.start_new_thread(driverFunc.driverEudatCall, (submittedJob[2], submittedJob[3])) 
             elif submittedJob[4] == '2':
                log("New job has been received. IPFS with miniLock call |" + time.ctime(), "green");
                driverFunc.driverIpfsCall(submittedJob[2], submittedJob[3], submittedJob[4]);
                #thread.start_new_thread(driverFunc.driverIpfsCall, (submittedJob[2], submittedJob[3], submittedJob[4], submittedJob[5]))
             elif submittedJob[4] == '3': 
                log("New job has been received. GitHub call |" + time.ctime(), "green");
                driverFunc.driverGithubCall(submittedJob[2], submittedJob[3], submittedJob[4]);
             elif submittedJob[4] == '4': 
                log("New job has been received. Googe Drive call |" + time.ctime(), "green");
                driverFunc.driverGdriveCall(submittedJob[2], submittedJob[3], submittedJob[4]);
       #}    
       
       if submittedJob != 0 and (int(maxVal) != 0): #{ 
          f_blockReadFrom = open(constants.BLOCK_READ_FROM_FILE, 'w'); # Updates the latest read block number      
          f_blockReadFrom.write(str(int(maxVal) + 1) + '\n'); # Python will convert \n to os.linesep
          f_blockReadFrom.close();
          blockReadFrom = str(int(maxVal) + 1);
       #}
              
       if isClusterReceivedJob == 0: #{ If there is no submitted job for the cluster, block start to read from current block number
          f_blockReadFrom = open(constants.BLOCK_READ_FROM_FILE, 'w'); # Updates the latest read block number
          f_blockReadFrom.write(str(currentBlockNumber) + '\n'); # Python will convert \n to os.linesep
          f_blockReadFrom.close();
          blockReadFrom = str(currentBlockNumber);
    #}
#}
