#!/usr/bin/env python3

import os, sys, subprocess, time, json, errno, glob, pwd
from shutil import copyfile
from dotenv import load_dotenv
from os.path import expanduser
home = expanduser("~")
load_dotenv(os.path.join(home + '/.eBlocBroker/', '.env')) # Load .env from the given path

WHOAMI     = os.getenv("WHOAMI")
EBLOCPATH  = os.getenv("EBLOCPATH")
LOG_PATH   = os.getenv("LOG_PATH") 
CLUSTER_ID = os.getenv("CLUSTER_ID")
GDRIVE     = os.getenv("GDRIVE")
RPC_PORT   = os.getenv("RPC_PORT")
POA_CHAIN  = os.getenv("POA_CHAIN")
OC_USER    = os.getenv("OC_USER")

GDRIVE_CLOUD_PATH = "/home/" + WHOAMI + "/foo" 
GDRIVE_METADATA   = "/home/" + WHOAMI + "/.gdrive" 
IPFS_REPO         = "/home/" + WHOAMI + "/.ipfs" 
HOME              = "/home/" + WHOAMI
OWN_CLOUD_PATH    = "/oc"

IPFS_USE                    = 0 # Should be '1', if caching into IPFS is open
PROGRAM_PATH                = '/var/eBlocBroker' 
JOBS_READ_FROM_FILE         = LOG_PATH + "/test.txt" 
CANCEL_JOBS_READ_FROM_FILE  = LOG_PATH + "/cancelledJobs.txt"
BLOCK_READ_FROM_FILE        = LOG_PATH + "/blockReadFrom.txt" 
CANCEL_BLOCK_READ_FROM_FILE = LOG_PATH + "/cancelledBlockReadFrom.txt" 

## Creates the hashmap.
job_state_code = {} 

# Add keys to the hashmap #https://slurm.schedmd.com/squeue.html
#                              = 0 # dummy as NULL.
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

def log(strIn, color=''):
    from colored import stylize
    from colored import fg
    if color != '':
        print(stylize(strIn, fg(color))) 
    else:
        print(strIn)
        
    txFile = open(LOG_PATH + '/transactions/clusterOut.txt', 'a') 
    txFile.write(strIn + "\n") 
    txFile.close() 

# enum: https://stackoverflow.com/a/1695250/2402577
def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    reverse = dict((value, key) for key, value in enums.items())
    enums['reverse_mapping'] = reverse
    return type('Enum', (), enums)

storageID = enum('ipfs', 'eudat', 'ipfs_miniLock', 'github', 'gdrive')
cacheType = enum('private', 'public', 'none', 'ipfs')

def runCommand(command, my_env=None):
    status=True
    if my_env is None:
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else :
        p = subprocess.Popen(command, env=my_env,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
    output, err = p.communicate()      
    if p.returncode != 0:
        status=False
        err = err.decode('utf-8')
        if err != '':
            log(err, 'red')
            
    return output.strip().decode('utf-8'), status

def silentremove(filename): # https://stackoverflow.com/a/10840586/2402577   
    try:
        os.remove(filename)
    except OSError as e: # this would be "except OSError, e:" before Python 2.6
        # if e.errno != errno.ENOENT: # errno.ENOENT = no such file or directory
        log(str(e), 'red')
        # raise # re-raise exception if a different error occurred
        pass

def removeFiles(filename):
   if "*" in filename: 
       for fl in glob.glob(filename):
           # print(fl)
           silentremove(fl) 
   else:
       silentremove(filename) 

def web3Exception(check): 
   while check  == 'ConnectionRefusedError' or check == 'notconnected':
      log('Error(web3)=' +  check + '. Please run geth on the background.', 'red')
      check = getJobInfo(lib.CLUSTER_ID, jobKey, index, eBlocBroker, web3)
      time.sleep(5)
      
   if check == 'BadFunctionCallOutput':
      log('Error(web3): ' +  check + '.', 'red')
      # sys.exit()

def isHashCached(ipfsHash):
    # cmd: ipfs refs local | grep -c 'Qmc2yZrduQapeK47vkNeT5pCYSXjsZ3x6yzK8an7JLiMq2'
    p1 = subprocess.Popen(['ipfs', 'refs', 'local'], stdout=subprocess.PIPE)
    #-----------
    p2 = subprocess.Popen(['grep', '-c', ipfsHash], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    #-----------
    out = p2.communicate()[0].decode('utf-8').strip()
    if out == '1':    
        return True
    else:
        return False
      
# Checks whether Slurm runs on the background or not, if not runs slurm
def isSlurmOn():
   while True:
      subprocess.run(['bash', 'checkSinfo.sh'])
      with open(LOG_PATH + '/checkSinfoOut.txt', 'r') as content_file:
         check = content_file.read()

      if not "PARTITION" in str(check):
         log("Error: sinfo returns emprty string, please run:\nsudo ./runSlurm.sh\n", "red")
         log('Error Message: \n' + check, "red")         
         log('Starting Slurm... \n', "green")
         subprocess.run(['sudo', 'bash', 'runSlurm.sh'])
      elif "sinfo: error" in str(check): 
         log("Error on munged: \n" + check)
         log("Please Do:\n")
         log("sudo munged -f")
         log("/etc/init.d/munge start")
      else:
         log('Slurm is on', 'green')
         break

def preexec_function():
    signal.signal(signal.SIGINT, signal.SIG_IGN)

def isTransactionPassed(web3, tx):
    receipt = web3.eth.getTransactionReceipt(tx)
    if receipt is None:
        return False
    
    if receipt['status'] == 1:
        return True
    else:
        return False
    
# Checks that does IPFS run on the background or not
def isIpfsOn():
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
      log('* Starting IPFS: nohup ipfs daemon --mount &', 'green')
      with open(LOG_PATH + '/ipfs.out', 'w') as stdout:
         subprocess.Popen(['nohup', 'ipfs', 'daemon', '--mount'],
                          stdout=stdout,
                          stderr=stdout,
                          preexec_fn=os.setpgrp)
         
      time.sleep(5)
      with open(LOG_PATH + '/ipfs.out', 'r') as content_file:
         log(content_file.read(), 'blue')
         
      # IPFS mounted at: /ipfs //cmd: sudo ipfs mount -f /ipfs      
      res = subprocess.check_output(['sudo', 'ipfs', 'mount', '-f', '/ipfs']).decode('utf-8').strip()
      log(res)      
   else:
      log("IPFS is already on.", 'green') 

def isRunExistInTar(tarPath):
    try:
        FNULL = open(os.devnull, 'w')
        res = subprocess.check_output(['tar', 'ztf', tarPath, '--wildcards', '*/run.sh'], stderr=FNULL).decode('utf-8').strip()
        FNULL.close()
        if res.count('/') == 1: # Main folder should contain the 'run.sh' file
            log('./run.sh exists under the parent folder', 'green')
            return True
        else:
            log('run.sh does not exist under the parent folder', 'red')
            return False            
    except:
        log('run.sh does not exist under the parent folder', 'red')
        return False

def sbatchCall(jobKey, index, storageID, shareToken, userID, resultsFolder, resultsFolderPrev, dataTransferIn,  eBlocBroker, web3):
   from contractCalls.getJobInfo import getJobInfo
   from datetime import datetime, timedelta   
   # cmd: date --date=1 seconds +%b %d %k:%M:%S %Y
   date = subprocess.check_output(['date', '--date=' + '1 seconds', '+%b %d %k:%M:%S %Y'],
                                  env={'LANG': 'en_us_88591'}).decode('utf-8').strip()
   log('Date=' + date)
   f = open(resultsFolderPrev + '/modifiedDate.txt', 'w') 
   f.write(date + '\n' )    
   f.close()   
   # cmd: echo date | date +%s
   p1 = subprocess.Popen(['echo', date], stdout=subprocess.PIPE)
   #-----------
   p2 = subprocess.Popen(['date', '+%s'], stdin=p1.stdout, stdout=subprocess.PIPE)
   p1.stdout.close()
   #-----------
   timestamp = p2.communicate()[0].decode('utf-8').strip()
   log('Timestamp=' + timestamp)
   f = open(resultsFolderPrev + '/timestamp.txt', 'w') 
   f.write(timestamp + '\n' )    
   f.close()
   if os.path.isfile(resultsFolderPrev + '/dataTransferIn.txt'):
       with open(resultsFolderPrev + '/dataTransferIn.txt') as json_file:
           data = json.load(json_file)
           dataTransferIn = data['dataTransferIn']
   else:
       data = {}
       data['dataTransferIn'] = dataTransferIn
       with open(resultsFolderPrev + '/dataTransferIn.txt', 'w') as outfile:
           json.dump(data, outfile)
           
   # print(dataTransferIn) 
   time.sleep(0.25)
   copyfile(resultsFolder + '/run.sh', resultsFolder + '/' + jobKey + '*' + str(index) + '*' + str(storageID) + '*' + shareToken + '.sh')
   jobInfo       = getJobInfo(CLUSTER_ID, jobKey, int(index), eBlocBroker, web3)
   jobCoreNum    = str(jobInfo['core'])
   coreSecondGas = timedelta(seconds=int((jobInfo['coreMinuteGas'] + 1) * 60))  # Client's requested seconds to run his/her job, 1 minute additional given.
   d             = datetime(1,1,1) + coreSecondGas 
   timeLimit     = str(int(d.day)-1) + '-' + str(d.hour) + ':' + str(d.minute) 
   log("timeLimit=" + str(timeLimit) + "| RequestedCoreNum=" + jobCoreNum)
   # Give permission to user that will send jobs to Slurm.
   subprocess.check_output(['sudo', 'chown', '-R', userID, resultsFolder])
   
   ## SLURM submit job, Real mode -N is used. For Emulator-mode -N use 'sbatch -c'   
   ## cmd: sudo su - $userID -c "cd $resultsFolder && sbatch -c$jobCoreNum $resultsFolder/${jobKey}*${index}*${storageID}*$shareToken.sh --mail-type=ALL   
   jobID = subprocess.check_output(['sudo', 'su', '-', userID, '-c',
                                    'cd' + ' ' + resultsFolder + ' && ' + 'sbatch -N' + jobCoreNum + ' ' + 
                                    resultsFolder + '/' + jobKey + '*' + str(index) + '*' + str(storageID) + '*' + shareToken + '.sh' + ' ' + 
                                    '--mail-type=ALL']).decode('utf-8').strip()
   jobID = jobID.split()[3]
   log('jobID=' + jobID)   
   try:
       # cmd: scontrol update jobid=$jobID TimeLimit=$timeLimit
       subprocess.run(['scontrol', 'update', 'jobid=' + jobID, 'TimeLimit=' + timeLimit], stderr=subprocess.STDOUT)
   except subprocess.CalledProcessError as e:
       log(e.output.decode('utf-8').strip())
      
   if not jobID.isdigit():
      # Detects an error on the SLURM side
      log("Error: jobID is not a digit.", 'red')
      return False
