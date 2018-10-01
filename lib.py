import os, sys, subprocess, time
from colored import stylize
from colored import fg
from dotenv import load_dotenv
load_dotenv()

WHOAMI     = os.getenv("WHOAMI")
EBLOCPATH  = os.getenv("EBLOCPATH")
LOG_PATH   = os.getenv("LOG_PATH") 
CLUSTER_ID = os.getenv("CLUSTER_ID")
GDRIVE     = os.getenv("GDRIVE")
RPC_PORT   = os.getenv("RPC_PORT")
POA_CHAIN  = os.getenv("POA_CHAIN")

OC = "/home/" + WHOAMI + "/ocCluster" 
GDRIVE_METADATA = "/home/" + WHOAMI + "/.gdrive" 
IPFS_REPO       = "/home/" + WHOAMI + "/.ipfs" 
OWN_CLOUD_PATH  = "/home/" + WHOAMI + "/.eBlocBroker/oc" 

IPFS_USE                    = 0
PROGRAM_PATH                = '/var/eBlocBroker' 
JOBS_READ_FROM_FILE         = LOG_PATH + "/test.txt" 
CANCEL_JOBS_READ_FROM_FILE  = LOG_PATH + "/cancelledJobs.txt"
BLOCK_READ_FROM_FILE        = LOG_PATH + "/blockReadFrom.txt" 
CANCEL_BLOCK_READ_FROM_FILE = LOG_PATH + "/cancelledBlockReadFrom.txt" 

## Creates the hashmap.
job_state_code = {} 

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

inv_job_state_code = {v: k for k, v in job_state_code.items()}

def log(strIn, color=''): #{
   if color != '':
      print(stylize(strIn, fg(color))) 
   else:
      print(strIn)

   txFile = open(LOG_PATH + '/transactions/clusterOut.txt', 'a') 
   txFile.write(strIn + "\n") 
   txFile.close() 
#}

def web3Exception(check): #{
   while check  is 'ConnectionRefusedError' or check is 'notconnected': #{
      log('Error(web3): ' +  check + '. Please run geth on the background.', 'red')
      check = getJobInfo(lib.CLUSTER_ID, jobKey, index, eBlocBroker, web3)
      time.sleep(5)
   #}
   if check is 'BadFunctionCallOutput': #{
      log('Error(web3): ' +  check + '.', 'red')
      # sys.exit()
   #}
#}
   
# Checks whether Slurm runs on the background or not, if not runs slurm
def isSlurmOn(): #{
   while True: #{
      subprocess.run(['bash', 'checkSinfo.sh'])
      with open(LOG_PATH + '/checkSinfoOut.txt', 'r') as content_file:
         check = content_file.read()

      if not "PARTITION" in str(check): #{
         log("Error: sinfo returns emprty string, please run:\nsudo ./runSlurm.sh\n", "red")
         log('Error Message: \n' + check, "red")
         subprocess.run(['sudo', 'bash', 'runSlurm.sh'])
      #}
      elif "sinfo: error" in str(check): #{
         log("Error on munged: \n" + check)
         log("Please Do:\n")
         log("sudo munged -f")
         log("/etc/init.d/munge start")
      #}
      else:
         log('Slurm is on', 'green')
         break
   #}
#}

def preexec_function():
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    
# Checks that does IPFS run on the background or not
def isIpfsOn(): #{
   # cmd: ps aux | grep '[i]pfs daemon' | wc -l
   p1 = subprocess.Popen(['ps', 'aux'], stdout=subprocess.PIPE)
   #-----------
   p2 = subprocess.Popen(['grep', '[i]pfs daemon'], stdin=p1.stdout, stdout=subprocess.PIPE)
   p1.stdout.close()
   #-----------
   p3 = subprocess.Popen(['wc', '-l'], stdin=p2.stdout,stdout=subprocess.PIPE)
   p2.stdout.close()
   #-----------
   check = p3.communicate()[0].decode('utf-8').strip()

   if int(check) == 0:
      log("Error: IPFS does not work on the background.", 'red') 
      log(" * Starting IPFS: nohup ipfs daemon &")
      with open(LOG_PATH + '/ipfs.out', 'w') as stdout:
         subprocess.Popen(['nohup', 'ipfs', 'daemon', '--mount'],
                          stdout=stdout,
                          stderr=stdout,
                          preexec_fn=os.setpgrp)      
      time.sleep(5)
      with open(LOG_PATH + '/ipfs.out', 'r') as content_file:
         log(content_file.read(), 'blue') 
   else:
      log("IPFS is already on.", 'green') 
#}
