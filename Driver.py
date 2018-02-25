#!/usr/bin/env python

from subprocess import call
import sys, os, time, subprocess, string, driverFunc, constants, thread

def logTest(strIn):
   print(strIn)
   txFile = open( constants.LOG_PATH + '/transactions/clusterOut.txt', 'a');
   txFile.write(strIn + "\n"); txFile.close();

def contractCall( val ):
   returnedVal = os.popen( val + "| node & echo $! >" + constants.LOG_PATH + "/my-app.pid").read().replace("\n", "").replace(" ", "");
   isRpcError(returnedVal);
   return returnedVal;
#sudo kill -9 $(cat /tmp/my-app.pid)

def isRpcError(inputStr):
   if(inputStr == "notconnected"):
      logTest("Error: Please run Parity or Geth on the background.")
      sys.exit()

# checks: does Driver.py run on the background
def isDriverOn(): 
   check = os.popen("ps aux | grep \'Driver.py\' | grep -v \'grep\' ").read().replace("\n", "");

   if(len(check) == 0):
      logTest( "Driver is already on" )
      sys.exit()

# checks: does IPFS run on the background or not
def isIpfsOn():
   check = os.popen("ps aux | grep \'ipfs daemon\' | grep -v \'grep\' ").read().replace("\n", "");
   if(len(check) == 0):
      logTest( "Error: IPFS does not work on the background. Please do: ipfs daemon & " )
      return False;
   return True;

# checks: does SLURM run on the background or not
def isSlurmOn(): 
   os.system("bash checkSinfo.sh")
   os.environ['logPath'] = constants.LOG_PATH;
   check                 = os.popen("cat $logPath/checkSinfoOut.txt").read()

   if not "PARTITION" in str(check):
      logTest("-------------------------- \n");
      logTest("Error: sinfo returns emprty string, please run \'sudo bash runSlurm.sh\'. \n");
      logTest( check );
      sys.exit();

   if "sinfo: error" in str(check):
      logTest("Error on munged: \n" + check)
      logTest("Please Do:\n")
      logTest("sudo munged -f")
      logTest("/etc/init.d/munge start")
      sys.exit()

yes = set(['yes','y', 'ye']);
no  = set(['no' ,'n'      ]);

isDriverOn();
isSlurmOn();
if( constants.IPFS_USE == 1 ):
   if( not isIpfsOn() ):
      sys.exit()

jobsReadFromPath = constants.JOBS_READ_FROM_FILE;
os.environ['jobsReadFromPath'] = jobsReadFromPath

eblocPath         = constants.EBLOCPATH;
header            = "var mylib = require('" + eblocPath + "/eBlocBrokerHeader.js')"; os.environ['header']     = header;
clusterId         = constants.CLUSTER_ID; os.environ['clusterId'] = clusterId

deployedBlockNumber   = contractCall('echo "$header; console.log( \'\' + mylib.getDeployedBlockNumber() )"');
#blockReadFromContract = contractCall('echo "$header; console.log( \'\' + mylib.getBlockReadFrom() )"'); #TODO: event'den cek
blockReadFromContract=str(0)

logTest("------------CLUSTER_ON------------")
logTest("deployedBlockNumber: " +  deployedBlockNumber)

if (not os.path.isfile(constants.BLOCK_READ_FROM_FILE)):
   f = open(constants.BLOCK_READ_FROM_FILE, 'w')
   f.write( deployedBlockNumber + "\n" )
   f.close()

f = open(constants.BLOCK_READ_FROM_FILE, 'r')
blockReadFromLocal = f.read().replace("\n", "");
f.close();

if (not blockReadFromLocal.isdigit()):
   logTest("Error: constants.BLOCK_READ_FROM_FILE is empty or contains and invalid value")
   logTest("> Would you like to read from contract's deployed block number? y/n")
   while True:
      choice = raw_input().lower()
      if choice in yes:
         blockReadFromLocal = deployedBlockNumber;
         f = open(constants.BLOCK_READ_FROM_FILE, 'w')
         f.write( deployedBlockNumber + "\n" )
         f.close()
         logTest("\n")
         break;
      elif choice in no:
         sys.exit()
      else:
         sys.stdout.write("Please respond with 'yes' or 'no'")


blockReadFrom = 0;
if (int(blockReadFromLocal) < int(blockReadFromContract)):
   blockReadFrom = blockReadFromContract
   #f = open(constants.BLOCK_READ_FROM_FILE, 'w')
   #f.write( blockReadFromContract + "\n" )  # python will convert \n to os.linesep
   #f.close()
else:
   blockReadFrom = blockReadFromLocal

#TODO: global job counter tut.
while True: #{
    if "Error" in blockReadFrom:
       logTest(blockReadFrom);
       sys.exit();

    clusterGainedAmount   = contractCall('echo "$header; console.log( \'\' + mylib.getClusterReceivedAmount(\'$clusterId\') )"');
    squeueStatus = os.popen("squeue").read();

    if "squeue: error:" in str(squeueStatus):
       logTest("SLURM is not running on the background, please run \'sudo bash runSlurm.sh\'. \n");
       logTest(squeueStatus);
       sys.exit();

    logTest("Current Slurm Running jobs status: \n" + squeueStatus);
    logTest("Current Time: " + time.ctime() + '| ClusterGainedAmount: ' + clusterGainedAmount);
    logTest("Waiting new job to come since block number: " + blockReadFrom);

    printFlag=0;
    currentBlockNumber = contractCall('echo "$header; console.log( \'\' + mylib.blockNumber )"');
    while(True):
       if (printFlag == 0):
          logTest( "Waiting currentBlockNumber to increment by one" );
          logTest( "Current BlockNumber: " + currentBlockNumber  + "; wanted Block Number: " + blockReadFrom);
          
       if (int(currentBlockNumber) >= int(blockReadFrom)):
          break;
       
       printFlag = 1;
       time.sleep(1);
       currentBlockNumber = contractCall('echo "$header; console.log( \'\' + mylib.blockNumber )"');
       logTest("Passed Incremented blockNumber...Continue waiting from block number: " + blockReadFrom);

    os.environ['blockReadFrom'] = str(blockReadFrom) # Starting reading event's location has been updated

    # Waits here until new job submitted into the cluster
    returnVal = contractCall('echo "$header; console.log( \'\' + mylib.LogJob( $blockReadFrom, \'$jobsReadFromPath\' ) )"'); 


    if os.path.isfile(jobsReadFromPath): #{    Waits until generated file on log is completed
       fR = open( jobsReadFromPath, 'r' )
       blockReadFrom = fR.read().replace("\n", "");
       fR.close();

       submittedJobs = blockReadFrom.split('?')

       submittedJob=0;
       maxVal = 0;
       for i in range( 0, (len(submittedJobs) - 1)  ): #{
          logTest("------------------------------------------------------------------")
          submittedJob = submittedJobs[i].split(' ');
          print(submittedJob[5])
          
          if (clusterId == submittedJob[1]): # Only obtain jobs that are submitted to the cluster
             logTest("BlockNum: " + submittedJob[0]  + " " + submittedJob[1] + " " + submittedJob[2] + " " + submittedJob[3] + " " + submittedJob[4] );

             if (int(submittedJob[0]) > int(maxVal)):
                maxVal = submittedJob[0]

             os.environ['jobKey']   = submittedJob[2]
             os.environ['index'] = submittedJob[3]

             jobInfo = contractCall('echo "$header; console.log( \'\' + mylib.getJobInfo( \'$clusterId\', \'$jobKey\', \'$index\' ) )"');
             jobInfo = jobInfo.split(',');

             # Checks isAlreadyCaptured job or not. If it is completed job do not obtain it
             if (jobInfo[0] == str(constants.job_state_code['PENDING'])): 
                if (submittedJob[4] == '0'):
                   logTest("New job has been recieved. IPFS call |" + time.ctime())
                   driverFunc.driverIpfsCall(submittedJob[2], submittedJob[3], submittedJob[4], submittedJob[5]); #TODO: could be called as a thread but its already fast
                elif (submittedJob[4] == '1'):
                   logTest("New job has been recieved. EUDAT call |" + time.ctime());
                   driverFunc.driverEudatCall( submittedJob[2], submittedJob[3]);
                   #thread.start_new_thread(driverFunc.driverEudatCall, (submittedJob[2], submittedJob[3], clusterId) ) #works
                elif (submittedJob[4] == '2'):
                   logTest("New job has been recieved. IPFS with miniLock call |" + time.ctime());
                   driverFunc.driverIpfsCall(submittedJob[2], submittedJob[3], submittedJob[4], submittedJob[5]); 
             else:
                logTest("Job is already captured and in process");
       #}
       
       # updates the latest read block number
       if( submittedJob != 0 and (int(maxVal) != 0) ): #{
          f_blockReadFrom = open(constants.BLOCK_READ_FROM_FILE, 'w')
          f_blockReadFrom.write(str(int(maxVal) + 1) + "\n")  # Python will convert \n to os.linesep
          f_blockReadFrom.close()

          blockReadFrom = str(int(maxVal) + 1)
       #}
    #}
#}
