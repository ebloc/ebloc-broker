#!/usr/bin/env python

from subprocess import call
import sys, os, time, subprocess, string, driverFunc, constants, _thread
from colored import stylize
from colored import fg
import hashlib
import sys, signal

sys.path.insert(0, 'contractCalls')
import LogJob
os.chdir('..');

# Running driverCancel.py on the background
if int(os.popen("ps aux | grep \'[d]riverCancel\' | grep \'python3\' | wc -l").read().rstrip('\n')) == 0:
   pro = subprocess.Popen(["python3","driverCancel.py"]);

# Paths =================================================================
jobsReadFromPath               = constants.JOBS_READ_FROM_FILE;
os.environ['jobsReadFromPath'] = jobsReadFromPath
contractCallPath               = constants.EBLOCPATH + '/contractCalls';
os.environ['eblocPath']        = constants.EBLOCPATH;
os.environ['contractCallPath'] = contractCallPath;
os.environ['logPath']          = constants.LOG_PATH;
os.environ['programPath']      = constants.PROGRAM_PATH;
# =======================================================================

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

def terminate(): #{
   log('Terminated')
   os.popen("sudo bash killall.sh").read(); # Kill all dependent processes and exit.

   # Following lines are added in case bash killall.sh does not work due to sudo:
   os.killpg(os.getpgid(pro.pid), signal.SIGTERM);  # Send the kill signal to all the process groups
   sys.exit();
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
      terminate();      
#}

# checks: does Driver.py runs on the background
def isDriverOn(): #{
   check = os.popen("ps aux | grep \'[D]river.py\' | grep \'python\' | wc -l").read().rstrip('\n');
   if int(check) > 1:
      log("Driver is already running.", 'green');
      terminate();
#}

# checks whether  Slurm runs on the background or not
def isSlurmOn(): #{
   os.system("bash checkSinfo.sh")  
   check = os.popen("cat $logPath/checkSinfoOut.txt").read();
   if not "PARTITION" in str(check): #{
      log("Error: sinfo returns emprty string, please run:\nsudo ./runSlurm.sh\n", "red");      
      log('Error Message: \n' + check, "red");
      terminate();
   #}   
   if "sinfo: error" in str(check): #{
      log("Error on munged: \n" + check);
      log("Please Do:\n");
      log("sudo munged -f");
      log("/etc/init.d/munge start");
      terminate();
   #}
#}

yes = set(['yes', 'y', 'ye']);
no  = set(['no' , 'n']);
if constants.WHOAMI == '' or constants.EBLOCPATH == '' or constants.CLUSTER_ID == '': #{
   print(stylize('Once please run:  ./initialize.sh \n', fg('red')));
   terminate();
#}

isDriverOn();
isSlurmOn();
isGethOn();
   
isContractExist = os.popen('$contractCallPath/isContractExist.py').read().rstrip('\n');
if 'False' in isContractExist:
   log('Please check that you are using eBloc blockchain.', 'red');
   terminate();

log('=' * int(int(columns) / 2  - 12)   + ' cluster session starts ' + '=' * int(int(columns) / 2 - 12), "green");
log('isWeb3Connected: ' + os.popen('$contractCallPath/isWeb3Connected.py').read().rstrip('\n'))
log('rootdir: ' + os.getcwd());
log('{0: <20}'.format('contractAddress:') + "\"" + os.popen('cat contractCalls/address.json').read().rstrip('\n') + "\"", "yellow");

if constants.IPFS_USE == 1:
   constants.isIpfsOn(os, time);
   
header = "var eBlocBroker = require('" + constants.EBLOCPATH + "/eBlocBrokerHeader.js')";
os.environ['header'] = header;

clusterAddress = constants.CLUSTER_ID;
os.environ['clusterAddress'] = clusterAddress;

isClusterExist = os.popen('$contractCallPath/isClusterExist.py $clusterAddress').read().rstrip('\n');

if "false" in isClusterExist.lower(): #{
   print(stylize("Error: Your Ethereum address '" + clusterAddress + "' \n"
                 "does not match with any cluster in eBlocBroker. Please register your \n" 
                 "cluster using your Ethereum Address in to the eBlocBroker. You can \n"   
                 "use 'contractCalls/registerCluster.py' script to register your cluster.", fg('red')));
   terminate();
#}

deployedBlockNumber = os.popen('$contractCallPath/getDeployedBlockNumber.py').read().rstrip('\n');
blockReadFromContract = str(0);

log('{0: <20}'.format('clusterAddress:') + "\"" + clusterAddress + "\"", "yellow");
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
         terminate()
      else:
         sys.stdout.write("Please respond with 'yes' or 'no'");
   #}
#}

blockReadFrom = 0;
if (int(blockReadFromLocal) < int(blockReadFromContract)):
   blockReadFrom = blockReadFromContract;
else:
   blockReadFrom = blockReadFromLocal;
             
clusterGainedAmountInit = os.popen('$contractCallPath/getClusterReceivedAmount.py $clusterAddress').read().rstrip('\n');

log('{0: <21}'.format('deployedBlockNumber:') +  deployedBlockNumber + "| Cluster's initial money: " + clusterGainedAmountInit)

os.system('rm -f $logPath/queuedJobs.txt && rm -f $jobsReadFromPath'); # Remove queuedJobs from previous test.
while True: #{    
    if "Error" in blockReadFrom:
       log(blockReadFrom);
       terminate();

    clusterGainedAmount = os.popen('$contractCallPath/getClusterReceivedAmount.py $clusterAddress').read().rstrip('\n');    
    squeueStatus        = os.popen("squeue").read();

    if "squeue: error:" in str(squeueStatus): #{
       log("SLURM is not running on the background, please run \'sudo ./runSlurm.sh\'. \n");
       log(squeueStatus);
       terminate();
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
    blockReadFrom = str(blockReadFrom); # Starting reading event's location has been updated
    # blockReadFrom = 875683; 
    slurmPendingJobCheck()
    
    loggedJobs = LogJob.run(blockReadFrom, clusterAddress)       
            
    print('isWeb3Connected: ' + os.popen('$contractCallPath/isWeb3Connected.py').read().rstrip('\n'))
    maxVal               = 0;
    isClusterReceivedJob = 0;
    counter              = 0;
        
    for i in range(0, len(loggedJobs)):
       runFlag = 0;
       isClusterReceivedJob = 1;
       log(str(counter) + ' ' + '-' * (int(columns) - 2), "green");
       counter += 1;

       log("BlockNum: " + str(loggedJobs[i]['blockNumber']) + " " + loggedJobs[i].args['clusterAddress'] + " " + loggedJobs[i].args['jobKey'] + " " +
           str(loggedJobs[i].args['index']) + " " + str(loggedJobs[i].args['storageID']) + " " + loggedJobs[i].args['desc']);

       if loggedJobs[i]['blockNumber'] > int(maxVal):
          maxVal = loggedJobs[i]['blockNumber']

       os.environ['jobKey'] = loggedJobs[i].args['jobKey'];
       os.environ['index']  = str(loggedJobs[i].args['index']);

       strCheck = os.popen('bash $eblocPath/strCheck.sh $jobKey').read();            
       jobInfo  = os.popen('$contractCallPath/getJobInfo.py $clusterAddress $jobKey $index 2>/dev/null 2>/dev/null').read().rstrip('\n').replace(" ", "")[1:-1];
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
       elif str(loggedJobs[i].args['storageID']) == '0':
          log("New job has been received. IPFS call |" + time.ctime(), "green")
          driverFunc.driverIpfsCall(loggedJobs[i].args['jobKey'], str(loggedJobs[i].args['index']), str(loggedJobs[i].args['storageID']), hashlib.md5(userID.encode('utf-8')).hexdigest()); 
       elif str(loggedJobs[i].args['storageID']) == '1':
          log("New job has been received. EUDAT call |" + time.ctime(), "green");
          driverFunc.driverEudatCall(loggedJobs[i].args['jobKey'], str(loggedJobs[i].args['index']), userInfo[4], hashlib.md5(userID.encode('utf-8')).hexdigest());
          #thread.start_new_thread(driverFunc.driverEudatCall, (loggedJobs[i].args['jobKey'], str(loggedJobs[i].args['index']))) 
       elif str(loggedJobs[i].args['storageID']) == '2':
          log("New job has been received. IPFS with miniLock call |" + time.ctime(), "green");
          driverFunc.driverIpfsCall(loggedJobs[i].args['jobKey'], str(loggedJobs[i].args['index']), str(loggedJobs[i].args['storageID']), hashlib.md5(userID.encode('utf-8')).hexdigest());
          #thread.start_new_thread(driverFunc.driverIpfsCall, (loggedJobs[i].args['jobKey'], str(loggedJobs[i].args['index']), str(loggedJobs[i].args['storageID']), submittedJob[5]))
       elif str(loggedJobs[i].args['storageID']) == '3': 
          log("New job has been received. GitHub call |" + time.ctime(), "green");
          driverFunc.driverGithubCall(loggedJobs[i].args['jobKey'], str(loggedJobs[i].args['index']), str(loggedJobs[i].args['storageID']), hashlib.md5(userID.encode('utf-8')).hexdigest());
       elif str(loggedJobs[i].args['storageID']) == '4': 
          log("New job has been received. Googe Drive call |" + time.ctime(), "green");
          driverFunc.driverGdriveCall(loggedJobs[i].args['jobKey'], str(loggedJobs[i].args['index']), str(loggedJobs[i].args['storageID']), hashlib.md5(userID.encode('utf-8')).hexdigest());
    #}    

    if len(loggedJobs) > 0 and int(maxVal) != 0: #{ 
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
