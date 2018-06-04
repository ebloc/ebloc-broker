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


# PROGRAM_PATH                = LOG_PATH + "/ipfsHashes"; LOG_PATH + "/USERS";
# PROGRAM_PATH                = LOG_PATH + "/USERS";
PROGRAM_PATH                = '/var/eBlocBroker';

IPFS_USE                    = 0;
JOBS_READ_FROM_FILE         = LOG_PATH + "/test.txt";
CANCEL_JOBS_READ_FROM_FILE  = LOG_PATH + "/cancelledJobs.txt"
BLOCK_READ_FROM_FILE        = LOG_PATH + "/blockReadFrom.txt";
CANCEL_BLOCK_READ_FROM_FILE = LOG_PATH + "/cancelledBlockReadFrom.txt";

## Creates the hashmap.
job_state_code = {};

# Add keys to the hashmap #https://slurm.schedmd.com/squeue.html
                             # = 0 # dummy as NULL.
job_state_code['COMPLETED']    = 1
job_state_code['REFUNDED']     = 2
job_state_code['PENDING']      = 3
job_state_code['RUNNING']      = 4
job_state_code['BOOT_FAIL']    = 5
job_state_code['CANCELLED']    = 6
job_state_code['CONFIGURING']  = 7
job_state_code['COMPLETING']   = 8
job_state_code['FAILED']       = 9
job_state_code['NODE_FAIL']    = 10
job_state_code['PREEMPTED']    = 11
job_state_code['REVOKED']      = 12
job_state_code['SPECIAL_EXIT'] = 13
job_state_code['STOPPED']      = 14
job_state_code['SUSPENDED']    = 15
job_state_code['TIMEOUT']      = 16

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
#}

# Checks that does IPFS run on the background or not
def isIpfsOn(os, time): #{
   check = os.popen("ps aux | grep \'[i]pfs daemon\' | wc -l").read().rstrip('\n');
   if int(check) == 0:
      log("Error: IPFS does not work on the background. Running: nohup ipfs daemon &", 'red');
      os.system('nohup ipfs daemon > ' + LOG_PATH + '/ipfs.out 2>&1 &');
      time.sleep(15);
      log(os.popen("cat " + LOG_PATH + "/ipfs.out").read(), 'blue');
   else:
      log("IPFS is already on.", 'green');
#}

def contractCall(val): #{   
   ret = os.popen('echo "$header; console.log(\'\' + ' + val + ")\" | /usr/local/bin/node & echo $! >" + LOG_PATH + "/my-app.pid").read().rstrip('\n').replace(" ", "");

   if ret == "notconnected": #{
      log("Error: Please run Parity or Geth on the background.", 'red')
      sys.exit();
   #}
   
   return ret;
#}
