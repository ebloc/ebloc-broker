#!/usr/bin/env python

from subprocess import call
import sys, os, time, subprocess, string, driverFunc, constants, _thread
from colored import stylize
from colored import fg

#rows, columns = os.popen('stty size', 'r').read().split();
columns = 100;

def log(strIn, color):
   if color != '':
      print(stylize(strIn, fg(color)));
   else:
      print(strIn)
      
   txFile = open(constants.LOG_PATH + '/transactions/clusterOut.txt', 'a');
   txFile.write(strIn + "\n");
   txFile.close();   

def contractCall(val):
   returnedVal = os.popen( val + "| node & echo $! >" + constants.LOG_PATH + "/my-app.pid").read().rstrip('\n').replace(" ", "");
   isRpcError(returnedVal);
   return returnedVal;

def isRpcError(inputStr):
   if(inputStr == "notconnected"):
      log("Error: Please run Parity or Geth on the background.")
      sys.exit()

# checks: does Driver.py run on the background
def isDriverOn(): 
   check = os.popen("ps aux | grep \'[D]river.py\' | wc -l").read().rstrip('\n');

   if int(check) > 1:
      log("Driver is already running.", "");
      #log("Driver is already on or multiple Drivers are launch. Please run:\nFor Daemon: bash runDaemon.sh\nFor Process: sudo bash run.sh", "");
      sys.exit();

# checks: does SLURM run on the background or not
def isSlurmOn(): 
   os.environ['logPath'] = constants.LOG_PATH;
   os.system("bash checkSinfo.sh")  
   check = os.popen("cat $logPath/checkSinfoOut.txt").read();

   if not "PARTITION" in str(check):
      log("Error: sinfo returns emprty string, please run:\nsudo bash runSlurm.sh\n", "");      
      log('Error Message: \n' + check, "");
      sys.exit();

   if "sinfo: error" in str(check):
      log("Error on munged: \n" + check, "")
      log("Please Do:\n", "")
      log("sudo munged -f", "")
      log("/etc/init.d/munge start", "")
      sys.exit()

yes = set(['yes', 'y', 'ye']);
no  = set(['no' , 'n']);

if constants.WHOAMI == '' or constants.EBLOCPATH == '' or constants.CLUSTER_ID == '':
   print('Once please run:  bash initialize.sh');
   sys.exit();

isContractExist = os.popen('$contractCallPath/isContractExist.py').read().rstrip('\n');

if 'False' in isContractExist:
   print('Please check that you are using eBloc blockchain.');
   sys.exit();

log('=' * int(int(columns) / 2  - 12)   + ' cluster session starts ' + '=' * int(int(columns) / 2 - 12), "green")
isDriverOn();
isSlurmOn();
if constants.IPFS_USE == 1:
   constants.isIpfsOn(os, time);

# Paths---------
jobsReadFromPath               = constants.JOBS_READ_FROM_FILE;
os.environ['jobsReadFromPath'] = jobsReadFromPath
contractCallPath               = constants.EBLOCPATH + '/contractCalls';
os.environ['contractCallPath'] = contractCallPath;
# ---------------
   
header    = "var eBlocBroker = require('" + constants.EBLOCPATH + "/eBlocBrokerHeader.js')"; os.environ['header'] = header;
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
blockReadFromContract=str(0)

log("clusterAddress: " +  clusterID, "yellow")

if not os.path.isfile(constants.BLOCK_READ_FROM_FILE): #{
   f = open(constants.BLOCK_READ_FROM_FILE, 'w')
   f.write( deployedBlockNumber + "\n")
   f.close()
#}

f = open(constants.BLOCK_READ_FROM_FILE, 'r')
blockReadFromLocal = f.read().rstrip('\n');
f.close();

if not blockReadFromLocal.isdigit(): #{
   log("Error: constants.BLOCK_READ_FROM_FILE is empty or contains and invalid value", "")
   log("> Would you like to read from contract's deployed block number? y/n", "")   
   while True: #{
      choice = input().lower()
      if choice in yes:
         blockReadFromLocal = deployedBlockNumber;
         f = open(constants.BLOCK_READ_FROM_FILE, 'w')
         f.write( deployedBlockNumber + "\n")
         f.close()
         log("\n", "")
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

log("deployedBlockNumber: " +  deployedBlockNumber + " |Cluster's initial money: " + clusterGainedAmountInit, "")
os.system('rm -f $jobsReadFromPath')
       
while True: #{
    if "Error" in blockReadFrom:
       log(blockReadFrom, "");
       sys.exit();

    clusterGainedAmount = os.popen('$contractCallPath/getClusterReceivedAmount.py $clusterID').read().rstrip('\n');
    squeueStatus        = os.popen("squeue").read();

    if "squeue: error:" in str(squeueStatus): #{
       log("SLURM is not running on the background, please run \'sudo bash runSlurm.sh\'. \n", "");
       log(squeueStatus, "");
       sys.exit();
    #}
    
    log("Current Slurm Running jobs status: \n" + squeueStatus, "");
    log('-' * int(columns), "green")
    log("Current Time: " + time.ctime() + '| ClusterGainedAmount: ' + str(int(clusterGainedAmount) - int(clusterGainedAmountInit)), "");
    log("Waiting new job to come since block number: " + blockReadFrom, "");

    printFlag          = 0;
    passedPrintFlag    = 0;
    currentBlockNumber = os.popen('$contractCallPath/blockNumber.py').read().rstrip('\n');
    
    while True: #{
       if (printFlag == 0):
          log("Waiting new block to increment by one.", "");
          log("Current BlockNumber: " + currentBlockNumber  + "| sync from block number: " + blockReadFrom, "");
          
       if int(currentBlockNumber) >= int(blockReadFrom):
          break;
       
       printFlag = 1;
       time.sleep(2);
       currentBlockNumber = os.popen('$contractCallPath/blockNumber.py').read().rstrip('\n');

       if (passedPrintFlag == 0):
          log("Passed incremented block number... Continue to wait from block number: " + blockReadFrom, "");
          passedPrintFlag = 1;
    #}
    
    passedPrintFlag = 0;      
    os.environ['blockReadFrom'] = str(blockReadFrom) # Starting reading event's location has been updated

    # Waits here until new job submitted into the cluster
    returnVal = contractCall('echo "$header; console.log(\'\' + eBlocBroker.LogJob($blockReadFrom, \'$jobsReadFromPath\'))"'); 
    
    if os.path.isfile(jobsReadFromPath): #{ Waits until generated file on log is completed
       fR = open(jobsReadFromPath, 'r')
       blockReadFrom = fR.read().rstrip('\n');
       fR.close();

       submittedJob         = 0;
       submittedJobs        = blockReadFrom.split('?');
       maxVal               = 0;       
       isClusterRecievedJob = 0;

       for i in range(0, (len(submittedJobs) - 1)): #{
          submittedJob = submittedJobs[i].split(' ');          
          if clusterID == submittedJob[1]: # Only obtain jobs that are submitted to the cluster
             isClusterRecievedJob = 1;
             log('-' * int(columns), "green")
             log("BlockNum: " + submittedJob[0].rstrip('\n') + " " + submittedJob[1] + " " + submittedJob[2] + " " + submittedJob[3] + " " + submittedJob[4], "");

             if int(submittedJob[0]) > int(maxVal):
                maxVal = submittedJob[0]

             os.environ['jobKey'] = submittedJob[2];
             os.environ['index']  = submittedJob[3];
             
             jobInfo = os.popen('$contractCallPath/getJobInfo.py $clusterID $jobKey $index 2>/dev/null').read().rstrip('\n').replace(" ","")[1:-1];         
             jobInfo = jobInfo.split(',');
             
             # Checks isAlreadyCaptured job or not. If it is completed job do not obtain it
             if (jobInfo[0] == str(constants.job_state_code['PENDING'])): 
                if (submittedJob[4] == '0'):
                   log("New job has been recieved. IPFS call |" + time.ctime(), "")
                   driverFunc.driverIpfsCall(submittedJob[2], submittedJob[3], submittedJob[4], submittedJob[5]); 
                elif (submittedJob[4] == '1'):
                   log("New job has been recieved. EUDAT call |" + time.ctime(), "");
                   driverFunc.driverEudatCall(submittedJob[2], submittedJob[3]);
                   #thread.start_new_thread(driverFunc.driverEudatCall, (submittedJob[2], submittedJob[3])) 
                elif (submittedJob[4] == '2'):
                   log("New job has been recieved. IPFS with miniLock call |" + time.ctime(), "");
                   driverFunc.driverIpfsCall(submittedJob[2], submittedJob[3], submittedJob[4], submittedJob[5]);
                   #thread.start_new_thread(driverFunc.driverIpfsCall, (submittedJob[2], submittedJob[3], submittedJob[4], submittedJob[5]))
                elif (submittedJob[4] == '3'): 
                   log("New job has been recieved. GitHub call |" + time.ctime(), "");
                   driverFunc.driverGithubCall(submittedJob[2], submittedJob[3], submittedJob[4]);
                elif (submittedJob[4] == '4'): 
                   log("New job has been recieved. gdrive call |" + time.ctime(), "");
                   driverFunc.driverGdriveCall(submittedJob[2], submittedJob[3], submittedJob[4]);
             else:
                log("Job is already captured and in process or completed", "");
       #}    
       
       if submittedJob != 0 and (int(maxVal) != 0): #{ 
          f_blockReadFrom = open(constants.BLOCK_READ_FROM_FILE, 'w') # Updates the latest read block number      
          f_blockReadFrom.write(str(int(maxVal) + 1) + "\n") # Python will convert \n to os.linesep
          f_blockReadFrom.close()          
          blockReadFrom = str(int(maxVal) + 1)
       #}
              
       if isClusterRecievedJob == 0: #{ If there is no submitted job for the cluster, block start to read from current block number
          f_blockReadFrom = open(constants.BLOCK_READ_FROM_FILE, 'w') # Updates the latest read block number
          f_blockReadFrom.write(str(currentBlockNumber) + "\n") # Python will convert \n to os.linesep
          f_blockReadFrom.close()
          blockReadFrom = str(currentBlockNumber)
    #}
#}
