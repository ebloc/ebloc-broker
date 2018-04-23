import os, sys, subprocess;
from colored import stylize
from colored import fg

WHOAMI=""
EBLOCPATH=""
CLUSTER_ID=""
GDRIVE=""
RPC_PORT=8545

GDRIVE_METADATA ="/home/" + WHOAMI + "/.gdrive";
IPFS_REPO       ="/home/" + WHOAMI + "/.ipfs";
LOG_PATH        ="/home/" + WHOAMI + "/.eBlocBroker";    
OWN_CLOUD_PATH  ="/home/" + WHOAMI + "/.eBlocBroker/oc";


PROGRAM_PATH         = LOG_PATH + "/ipfsHashes" 
JOBS_READ_FROM_FILE  = LOG_PATH + "/test.txt"
BLOCK_READ_FROM_FILE = LOG_PATH + "/blockReadFrom.txt";

IPFS_USE             = 0;


## Creates the hashmap.
job_state_code = {};

# Add keys to the hashmap #https://slurm.schedmd.com/squeue.html
                             # = 0 #dummy do nothing
job_state_code['COMPLETED']    = 1
job_state_code['PENDING']      = 2
job_state_code['RUNNING']      = 3
job_state_code['BOOT_FAIL']    = 4
job_state_code['CANCELLED']    = 5
job_state_code['CONFIGURING']  = 6
job_state_code['COMPLETING']   = 7
job_state_code['FAILED']       = 8
job_state_code['NODE_FAIL']    = 9
job_state_code['PREEMPTED']    = 10
job_state_code['REVOKED']      = 11
job_state_code['SPECIAL_EXIT'] = 12
job_state_code['STOPPED']      = 13
job_state_code['SUSPENDED']    = 14
job_state_code['TIMEOUT']      = 15

header = "var eBlocBroker = require('" + EBLOCPATH + "/eBlocBrokerHeader.js')";
os.environ['header'] = header;

def log(strIn, color=''): #{
   if color != '':
      print(stylize(strIn, fg(color)));
   else:
      print(strIn)

   txFile = open(LOG_PATH + '/transactions/clusterOut.txt', 'a');
   txFile.write(strIn + "\n");
   txFile.close();

# checks: does IPFS run on the background or not
def isIpfsOn(os, time): #{
   check = os.popen("ps aux | grep \'[i]pfs daemon\' | wc -l").read().rstrip('\n');
   if int(check) == 0:
      log("Error: IPFS does not work on the background. Running: ipfs daemon &", 'red');
      os.system('ipfs daemon > ' + LOG_PATH + '/ipfs.out &');      
      time.sleep(15);
      log(os.popen("cat " + LOG_PATH + "/ipfs.out").read(), 'blue');
   else:
      log("IPFS is already on.", 'green');
#}

def contractCall(val): #{   
   returnedVal = os.popen('echo "$header; console.log(\'\' + ' + val + ")\" | /usr/local/bin/node & echo $! >" + LOG_PATH + "/my-app.pid").read().rstrip('\n').replace(" ", "");

   if returnedVal == "notconnected": #{
      log("Error: Please run Parity or Geth on the background.")
      sys.exit();
   #}
   
   return returnedVal;
#}


