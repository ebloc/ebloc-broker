#!/usr/bin/env python

from subprocess import call
import sys, os, time, subprocess, string, driverFunc, constants, _thread
from colored import stylize
from colored import fg
import hashlib

if int(os.popen("ps aux | grep \'[d]riverCancel\' | grep \'python3\' | wc -l").read().rstrip('\n')) == 0:
   subprocess.Popen(["python3","driverCancel.py"]);

# Paths ================================================================
jobsReadFromPath               = constants.JOBS_READ_FROM_FILE;
os.environ['jobsReadFromPath'] = jobsReadFromPath
contractCallPath               = constants.EBLOCPATH + '/contractCalls';
os.environ['eblocPath']        = constants.EBLOCPATH;
os.environ['contractCallPath'] = contractCallPath;
os.environ['logPath']          = constants.LOG_PATH;
os.environ['programPath']      = constants.PROGRAM_PATH;
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


def idleCoreNumber(printFlag=1): #{
    coreInfo = os.popen('sinfo -h -o%C').read().rstrip('\n');
    coreInfo = coreInfo.split("/");
    if len(coreInfo) != 0:
       idleCore = coreInfo[1];
       if printFlag == 1:
          log('AllocatedCores: ' + coreInfo[0] + '| IdleCores: ' + coreInfo[1] + '| OtherCores: ' + coreInfo[2] + '| TotalNumberOfCores: ' + coreInfo[3], 'blue');               
    else:
       log("sinfo return emptry string.", 'red');
       idleCore = 0;
    return idleCore;
#}   

def slurmPendingJobCheck(): #{
    idleCore  = idleCoreNumber();       
    printFlag = 0;    
    while idleCore == '0':  #{
       if printFlag == 0:
          log('Waiting running jobs to be completed...', 'blue');
          printFlag = 1;
       time.sleep(10);
       idleCore = idleCoreNumber(0);
    #}
#}

# checks whether geth runs on the background
def isGethOn(): #{  
   check = os.popen("ps aux | grep [g]eth | grep " + str(constants.RPC_PORT) + "| wc -l").read().rstrip('\n');
   if int(check) == 0:
      log("Geth is not running on the background.", 'red');
      sys.exit();      
#}

# checks: does Driver.py runs on the background
def isDriverOn(): #{
   check = os.popen("ps aux | grep \'[D]river.py\' | grep \'python\' | wc -l").read().rstrip('\n');
   if int(check) > 1:
      log("Driver is already running.", 'green');
      sys.exit();
#}

# checks whether  Slurm runs on the background or not
def isSlurmOn(): #{
   os.system("bash checkSinfo.sh")  
   check = os.popen("cat $logPath/checkSinfoOut.txt").read();
   if not "PARTITION" in str(check): #{
      log("Error: sinfo returns emprty string, please run:\nsudo bash runSlurm.sh\n", "red");      
      log('Error Message: \n' + check, "red");
      sys.exit();
   #}   
   if "sinfo: error" in str(check): #{
      log("Error on munged: \n" + check);
      log("Please Do:\n");
      log("sudo munged -f");
      log("/etc/init.d/munge start");
      sys.exit();
   #}
#}

yes = set(['yes', 'y', 'ye']);
no  = set(['no' , 'n']);
if constants.WHOAMI == '' or constants.EBLOCPATH == '' or constants.CLUSTER_ID == '': #{
   print(stylize('Once please run:  bash initialize.sh \n', fg('red')));
   sys.exit();
#}

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
   
header = "var eBlocBroker = require('" + constants.EBLOCPATH + "/eBlocBrokerHeader.js')";
os.environ['header'] = header;

clusterID = constants.CLUSTER_ID;
os.environ['clusterID'] = clusterID;

isClusterExist = os.popen('$contractCallPath/isClusterExist.py $clusterID').read().rstrip('\n');

if "false" in isClusterExist.lower(): #{
   print(stylize("Error: Your Ethereum address '" + clusterID + "' \n"
                 "does not match with any cluster in eBlocBroker. Please register your \n" 
                 "cluster using your Ethereum Address in to the eBlocBroker. You can \n"   
                 "use 'contractCalls/registerCluster.py' script to register your cluster.", fg('red')));
   sys.exit();
#}

deployedBlockNumber = os.popen('$contractCallPath/getDeployedBlockNumber.py').read().rstrip('\n');
blockReadFromContract = str(0);

log('{0: <21}'.format('clusterAddress:') +  clusterID, "yellow")
if not os.path.isfile(constants.BLOCK_READ_FROM_FILE): #{
   f = open(constants.BLOCK_READ_FROM_FILE, 'w')
   f.write(deployedBlockNumber + "\n")
   f.close()
#}

f = open(constants.BLOCK_READ_FROM_FILE, 'r');
blockReadFromLocal = f.read().rstrip('\n');
f.close();

if not blockReadFromLocal.isdigit(): #{
   log("Error: constants.BLOCK_READ_FROM_FILE is empty or contains and invalid value")
   log("#> Would you like to read from contract's deployed block number? y/n")   
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
    idleCoreNumber();
    
    log("Current Slurm Running jobs status: \n" + squeueStatus);
    log('-' * int(columns), "green")
    if 'notconnected' != clusterGainedAmount:
       log("Current Time: " + time.ctime() + '| ClusterGainedAmount: ' + str(int(clusterGainedAmount) - int(clusterGainedAmountInit)));
    log("Waiting new job to come since block number: " + blockReadFrom);
    
    currentBlockNumber = os.popen('$contractCallPath/blockNumber.py').read().rstrip('\n');
    log("Waiting new block to increment by one.");
    log("Current BlockNumber: " + currentBlockNumber  + "| sync from block number: " + blockReadFrom);
    
    while int(currentBlockNumber) < int(blockReadFrom): #{          
       time.sleep(2);
       currentBlockNumber = os.popen('$contractCallPath/blockNumber.py').read().rstrip('\n');
    #}    
    log("Passed incremented block number... Continue to wait from block number: " + blockReadFrom);
   
    os.environ['blockReadFrom'] = str(blockReadFrom) # Starting reading event's location has been updated
    slurmPendingJobCheck()
    
    constants.contractCall('eBlocBroker.LogJob($blockReadFrom, \'$jobsReadFromPath\')'); # Waits here until new job submitted into the cluster
    print('isWeb3Connected: ' + os.popen('$contractCallPath/isWeb3Connected.py').read().rstrip('\n'))
    if os.path.isfile(jobsReadFromPath): #{ Waits until generated file on log is completed       
       submittedJobs = set() # holds lines already seen
       for line in open(jobsReadFromPath, "r"): #{
          if line not in submittedJobs: # not a duplicate
             submittedJobs.add(line)
       #}
       
       submittedJobs        = sorted(submittedJobs);            
       maxVal               = 0;       
       isClusterReceivedJob = 0;       
       submittedJob         = 0;
       counter              = 0;

       for e in submittedJobs: #{
          runFlag = 0;
          submittedJob = e.rstrip('\n').split(' ');          
          if clusterID == submittedJob[1]: #{ Only obtain jobs that are submitted to the cluster
             isClusterReceivedJob = 1;
             log(str(counter) + ' ' + '-' * (int(columns) - 2), "green");
             counter += 1;
             log("BlockNum: " + submittedJob[0].rstrip('\n') + " " + submittedJob[1] + " " + submittedJob[2] + " " + submittedJob[3] + " " + submittedJob[4]);

             if int(submittedJob[0]) > int(maxVal):
                maxVal = submittedJob[0]

             os.environ['jobKey'] = submittedJob[2];
             os.environ['index']  = submittedJob[3];

             strCheck = os.popen('bash $eblocPath/strCheck.sh $jobKey').read();            
             jobInfo  = os.popen('$contractCallPath/getJobInfo.py $clusterID $jobKey $index 2>/dev/null 2>/dev/null').read().rstrip('\n').replace(" ", "")[1:-1];
             userID   = "";
             if not ',' in jobInfo or jobInfo == '': 
                log("jobInfo is returned as empty string. Geth might be closed", 'red');
                runFlag = 1;
             else: #{
                jobInfo = jobInfo.split(',');
                log('jobOwner/userID: ' +  jobInfo[6].replace("u'", "").replace("'", ""));
                
                userID = jobInfo[6].replace("u'", "").replace("'", "");
                os.environ['userID'] = jobInfo[6].replace("u'", "").replace("'", "");
             
                isUserExist = os.popen('$contractCallPath/isUserExist.py $userID 2>/dev/null').read().rstrip('\n');             
                userInfo    = os.popen('$contractCallPath/getUserInfo.py $userID 1 2>/dev/null').read().rstrip('\n').replace(" ", "");
                userInfo    = userInfo.split(',');            

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
                print(os.popen('sudo bash user.sh $userID $programPath').read()); # Create user and its work directory.
             #}
                         
             if runFlag == 1:
                pass;
             elif submittedJob[4] == '0':
                log("New job has been received. IPFS call |" + time.ctime(), "green")
                driverFunc.driverIpfsCall(submittedJob[2], submittedJob[3], submittedJob[4], hashlib.md5(userID.encode('utf-8')).hexdigest()); 
             elif submittedJob[4] == '1':
                log("New job has been received. EUDAT call |" + time.ctime(), "green");
                driverFunc.driverEudatCall(submittedJob[2], submittedJob[3], userInfo[4], hashlib.md5(userID.encode('utf-8')).hexdigest());
                #thread.start_new_thread(driverFunc.driverEudatCall, (submittedJob[2], submittedJob[3])) 
             elif submittedJob[4] == '2':
                log("New job has been received. IPFS with miniLock call |" + time.ctime(), "green");
                driverFunc.driverIpfsCall(submittedJob[2], submittedJob[3], submittedJob[4], hashlib.md5(userID.encode('utf-8')).hexdigest());
                #thread.start_new_thread(driverFunc.driverIpfsCall, (submittedJob[2], submittedJob[3], submittedJob[4], submittedJob[5]))
             elif submittedJob[4] == '3': 
                log("New job has been received. GitHub call |" + time.ctime(), "green");
                driverFunc.driverGithubCall(submittedJob[2], submittedJob[3], submittedJob[4], hashlib.md5(userID.encode('utf-8')).hexdigest());
             elif submittedJob[4] == '4': 
                log("New job has been received. Googe Drive call |" + time.ctime(), "green");
                driverFunc.driverGdriveCall(submittedJob[2], submittedJob[3], submittedJob[4], hashlib.md5(userID.encode('utf-8')).hexdigest());
       #}    
       
       if submittedJob != 0 and int(maxVal) != 0: #{ 
          f_blockReadFrom = open(constants.BLOCK_READ_FROM_FILE, 'w'); # Updates the latest read block number      
          f_blockReadFrom.write(str(int(maxVal) + 1) + '\n'); 
          f_blockReadFrom.close();
          blockReadFrom = str(int(maxVal) + 1);
       #}
              
       if isClusterReceivedJob == 0: #{ If there is no submitted job for the cluster, block start to read from current block number
          f_blockReadFrom = open(constants.BLOCK_READ_FROM_FILE, 'w'); # Updates the latest read block number
          f_blockReadFrom.write(str(currentBlockNumber) + '\n');
          f_blockReadFrom.close();
          blockReadFrom = str(currentBlockNumber);
    #}
#}
