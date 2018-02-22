WHOAMI          = "alper"
CLUSTER_ID      = "0xda1e61e853bb8d63b1426295f59cb45a34425b63"
EBLOCPATH       = "/home/" + WHOAMI + "/eBlocBroker";
IPFS_REPO       = "/home/" + WHOAMI + "/.ipfs";
LOG_PATH        = "/home/" + WHOAMI + "/.eBlocBroker";    
OWN_CLOUD_PATH  = "/home/" + WHOAMI + "/.eBlocBroker/oc"; 

PROGRAM_PATH         = LOG_PATH + "/ipfsHashes" 
JOBS_READ_FROM_FILE  = LOG_PATH + "/test.txt"
BLOCK_READ_FROM_FILE = LOG_PATH + "/blockReadFrom.txt";
IPFS_USE             = 0

## Create the hashmap
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
