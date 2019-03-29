#!/usr/bin/env python3

import pwd, os, sys
import owncloud, json
import time, subprocess, string, driverFunc, lib, _thread
import hashlib
import sys, signal

from subprocess import call
from colored import stylize
from colored import fg
from imports import connectEblocBroker
from imports import getWeb3
from driverEudat import driverEudat
from driverGdrive import driverGdrive

sys.path.insert(0, './contractCalls')
from contractCalls.getClusterReceivedAmount import getClusterReceivedAmount
from contractCalls.getDeployedBlockNumber   import getDeployedBlockNumber
from contractCalls.isContractExist          import isContractExist
from contractCalls.isClusterExist           import isClusterExist
from contractCalls.blockNumber              import blockNumber
from contractCalls.getJobInfo               import getJobInfo
from contractCalls.isUserExist              import isUserExist
from contractCalls.getUserInfo              import getUserInfo
from contractCalls.isWeb3Connected          import isWeb3Connected
from contractCalls.LogJob                   import runLogJob

web3        = getWeb3()
eBlocBroker = connectEblocBroker(web3)
driverCancelProcess   = None
driverReceiverProcess = None
oc                    = None
my_env = os.environ.copy()

# Dummy sudo command to get the password when session starts
subprocess.run(['sudo', 'printf', '']) 

"""Run DriverCancel daemon on the background."""
def runDriverCancel():
	# cmd: ps aux | grep \'[d]riverCancel\' | grep \'python3\' | wc -l 
    p1 = subprocess.Popen(['ps', 'aux'], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(['grep', '[d]riverCancel'], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    p3 = subprocess.Popen(['grep', 'python3'], stdin=p2.stdout,stdout=subprocess.PIPE)
    p2.stdout.close()
    p4 = subprocess.Popen(['wc', '-l'], stdin=p3.stdout,stdout=subprocess.PIPE)
    p3.stdout.close()
    out = p4.communicate()[0].decode('utf-8').strip()
    if int(out) == 0:
        # Running driverCancel.py on the background if it is not already
        driverCancelProcess = subprocess.Popen(['python3','driverCancel.py'])

def runWhisperStateReceiver():
    if not os.path.isfile(lib.HOME + '/.eBlocBroker/whisperInfo.txt'):
        # First time running:
        log('Please first run: scripts/whisperInitialize.py')
        terminate()
    else:
        with open(lib.HOME + '/.eBlocBroker/whisperInfo.txt') as json_file:
            data = json.load(json_file)
            
        kId = data['kId']
        publicKey = data['publicKey']
        if not web3.shh.hasKeyPair(kId):
            log("Error: Whisper node's private key of a key pair did not match with the given ID", 'red')
            log('Please first run: python scripts/whisperInitialize.py', 'red')
            terminate()            
            
    # cmd: ps aux | grep \'[d]riverCancel\' | grep \'python3\' | wc -l 
    p1 = subprocess.Popen(['ps', 'aux'], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(['grep', '[d]riverReceiver'], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    p3 = subprocess.Popen(['grep', 'python'], stdin=p2.stdout,stdout=subprocess.PIPE)
    p2.stdout.close()
    p4 = subprocess.Popen(['wc', '-l'], stdin=p3.stdout,stdout=subprocess.PIPE)
    p3.stdout.close()
    out = p4.communicate()[0].decode('utf-8').strip()
    # ----------------------------------------------------------------
    if int(out) == 0:
        # Running driverCancel.py on the background
        driverReceiverProcess = subprocess.Popen(['python3','whisperStateReceiver.py', '0']) #TODO: should be '0' to store log at a file and not print output
		
# res = subprocess.check_output(['stty', 'size']).decode('utf-8').strip()
# rows = res[0] columns = res[1]
columns = 100

def log(strIn, color=''): 
    if color != '':
        print(stylize(strIn, fg(color)))
    else:
        print(strIn)
        
    txFile = open(lib.LOG_PATH + '/transactions/clusterOut.txt', 'a')
    txFile.write(strIn + '\n')
    txFile.close()

def terminate():
	log('Terminated')
	subprocess.run(['sudo', 'bash', 'killall.sh']) # Kill all dependent processes and exit
	""" Following line is added, in case ./killall.sh does not work due to sudo.
	Send the kill signal to all the process groups. """
	os.killpg(os.getpgid(driverCancelProcess.pid),   signal.SIGTERM)
	os.killpg(os.getpgid(driverReceiverProcess.pid), signal.SIGTERM)	
	sys.exit()

def idleCoreNumber(printFlag=1):
    # cmd: sinfo -h -o%C
    coreInfo, status = lib.runCommand(['sinfo', '-h', '-o%C'])
    coreInfo = coreInfo.split('/')    
    if len(coreInfo) != 0:
       idleCore = coreInfo[1]
       if printFlag == 1:
          log('AllocatedCores: ' + coreInfo[0] + '| IdleCores: ' + coreInfo[1] +
              '| OtherCores: ' + coreInfo[2] + '| TotalNumberOfCores: ' + coreInfo[3], 'blue')
    else:
       log('sinfo return emptry string.', 'red')
       idleCore = 0
       
    return idleCore

def slurmPendingJobCheck(): 
    idleCore  = idleCoreNumber()       
    printFlag = 0    
    while idleCore == '0':
       if printFlag == 0:
          log('Waiting running jobs to be completed...', 'blue')
          printFlag = 1
       time.sleep(10)
       idleCore = idleCoreNumber(0)

# Checks whether geth runs on the background
def isGethOn():
   # cmd: ps aux | grep [g]eth | grep '8545' | wc -l
   p1 = subprocess.Popen(['ps', 'aux'], stdout=subprocess.PIPE)
   #-----------
   p2 = subprocess.Popen(['grep', '[g]eth'], stdin=p1.stdout, stdout=subprocess.PIPE)
   p1.stdout.close()
   #-----------
   p3 = subprocess.Popen(['grep', str(lib.RPC_PORT)], stdin=p2.stdout,stdout=subprocess.PIPE)
   p2.stdout.close()
   #-----------
   p4 = subprocess.Popen(['wc', '-l'], stdin=p3.stdout,stdout=subprocess.PIPE)
   p3.stdout.close()
   #-----------
   out = p4.communicate()[0].decode('utf-8').strip()
   
   if int(out) == 0:
      log("Geth is not running on the background.", 'red')
      lib.terminate()      

# Checks: does Driver.py runs on the background
def isDriverOn(): 
   # cmd: ps aux | grep \'[D]river.py\' | grep \'python\' | wc -l
   p1 = subprocess.Popen(['ps', 'aux'], stdout=subprocess.PIPE)
   #-----------
   p2 = subprocess.Popen(['grep', '[D]river.py'], stdin=p1.stdout, stdout=subprocess.PIPE)
   p1.stdout.close()
   #-----------
   p3 = subprocess.Popen(['grep', 'python'], stdin=p2.stdout,stdout=subprocess.PIPE)
   p2.stdout.close()
   #-----------
   p4 = subprocess.Popen(['wc', '-l'], stdin=p3.stdout,stdout=subprocess.PIPE)
   p3.stdout.close()
   #-----------
   out = p4.communicate()[0].decode('utf-8').strip()
   
   if int(out) > 1:
      log("Driver is already running.", 'green')

def eudatLoginAndCheck():
    global oc
    if lib.OC_USER is None or lib.OC_USER == "":
        log("OC_USER is not set in .env", "red")
        sys.exit()
        
    log("Login into owncloud...")
    with open(lib.EBLOCPATH + '/eudatPassword.txt', 'r') as content_file:
        password = content_file.read().strip()
        
    oc = owncloud.Client('https://b2drop.eudat.eu/') 
    oc.login(lib.OC_USER, password)  # Unlocks EUDAT account    
    password = None
    try:
        oc.list('.')
    except subprocess.CalledProcessError as e:
        log(e.output.decode('utf-8').strip(), 'red')        
        sys.exit()
        
# Startup functions are called
def startup():    
    isDriverOn()
    lib.isSlurmOn()
    isGethOn()
    # runDriverCancel()    
    runWhisperStateReceiver()
    if lib.EUDAT_USE:
        eudatLoginAndCheck()

yes = set(['yes', 'y', 'ye'])
no  = set(['no' , 'n'])
if lib.WHOAMI == '' or lib.EBLOCPATH == '' or lib.CLUSTER_ID == '': 
   print(stylize('Once please run:  ./initialize.sh \n', fg('red')))
   terminate()

log('=' * int(int(columns) / 2 - 12) + ' cluster session starts ' +
    '=' * int(int(columns) / 2 - 12), 'green')

startup()
isContractExist = isContractExist(web3)
if not isContractExist:
   log("Please check that you are using eBloc blockchain.", 'red')
   terminate()

log('isWeb3Connected: ' + str(isWeb3Connected(web3)))
log('rootdir: ' + os.getcwd())
with open('contractCalls/address.json', 'r') as content_file:
   log('{0: <20}'.format('contractAddress:') + '"' + content_file.read().strip() + '"', "yellow")

if lib.IPFS_USE:
   lib.isIpfsOn()

clusterAddress = lib.CLUSTER_ID
isClusterExist = isClusterExist(clusterAddress, eBlocBroker, web3)

if "false" in isClusterExist.lower():
   print(stylize("Error: Your Ethereum address '" + clusterAddress + "' \n"
                 "does not match with any cluster in eBlocBroker. Please register your \n" 
                 "cluster using your Ethereum Address in to the eBlocBroker. You can \n"   
                 "use 'contractCalls/registerCluster.py' script to register your cluster.", fg('red')))
   terminate()

deployedBlockNumber   = str(getDeployedBlockNumber(eBlocBroker))
blockReadFromContract = str(0)

log('{0: <20}'.format('clusterAddress:') + '"'+ clusterAddress + '"', 'yellow')
if not os.path.isfile(lib.BLOCK_READ_FROM_FILE): 
   f = open(lib.BLOCK_READ_FROM_FILE, 'w')
   f.write(deployedBlockNumber + "\n")
   f.close()

f = open(lib.BLOCK_READ_FROM_FILE, 'r')
blockReadFromLocal = f.read().rstrip('\n')
f.close()

if not blockReadFromLocal.isdigit(): 
   log("Error: lib.BLOCK_READ_FROM_FILE is empty or contains and invalid value")
   log("#> Would you like to read from contract's deployed block number? y/n")   
   while True: 
      choice = input().lower()
      if choice in yes:
         blockReadFromLocal = deployedBlockNumber
         f = open(lib.BLOCK_READ_FROM_FILE, 'w')
         f.write(deployedBlockNumber + "\n")
         f.close()
         log("\n")
         break
      elif choice in no:
         terminate()
      else:
         sys.stdout.write("Please respond with 'yes' or 'no'")

blockReadFrom = 0
if int(blockReadFromLocal) < int(blockReadFromContract):
   blockReadFrom = blockReadFromContract
else:
   blockReadFrom = blockReadFromLocal

clusterGainedAmountInit = getClusterReceivedAmount(clusterAddress, eBlocBroker, web3)
log('{0: <21}'.format('deployedBlockNumber:') +  deployedBlockNumber +
    "| Cluster's initial money: " + clusterGainedAmountInit)

while True:     
    if "Error" in blockReadFrom:
       log(blockReadFrom)
       terminate()

    clusterGainedAmount = getClusterReceivedAmount(clusterAddress, eBlocBroker, web3) 
    squeueStatus,status = lib.runCommand(['squeue'])    
    if "squeue: error:" in str(squeueStatus):
       log("SLURM is not running on the background, please run: sudo ./runSlurm.sh. \n")
       log(squeueStatus)
       terminate()
       
    idleCoreNumber()    
    log("Current Slurm Running jobs status: \n" + squeueStatus)
    log('-' * int(columns), "green")
    if 'notconnected' != clusterGainedAmount:
       log("Current Time: " + time.ctime() + "| ClusterGainedAmount: " +
           str(int(clusterGainedAmount) - int(clusterGainedAmountInit)))
       
    log("Waiting new job to come since block number: " + blockReadFrom, 'green')    
    currentBlockNumber = blockNumber() 
    log("Waiting new block to increment by one.")
    log("Current BlockNumber: " + currentBlockNumber  + "| sync from block number: " + blockReadFrom)
    while int(currentBlockNumber) < int(blockReadFrom):
       time.sleep(2)
       currentBlockNumber = blockNumber(web3)

    log("Passed incremented block number... Continue to wait from block number: " + blockReadFrom)   
    blockReadFrom = str(blockReadFrom) # Starting reading event's location has been updated
    # blockReadFrom = 1094262 # used for test purposes
    slurmPendingJobCheck()    
    loggedJobs = runLogJob(blockReadFrom, clusterAddress, eBlocBroker)       
    print('isWeb3Connected: ' + str(isWeb3Connected(web3)))
    maxVal               = 0
    isClusterReceivedJob = 0
    counter              = 0        
    for i in range(0, len(loggedJobs)):
       runFlag = 0
       isClusterReceivedJob = 1
       log(str(counter) + ' ' + '-' * (int(columns) - 2), "green")
       counter += 1
       
       log('BlockNum: ' + str(loggedJobs[i]['blockNumber']) + '\n' +
           'clusterAddress: ' + loggedJobs[i].args['clusterAddress'] + '\n' +
           'jobKey: ' + loggedJobs[i].args['jobKey'] + '\n' +
           'index: ' + str(loggedJobs[i].args['index']) + '\n' +
           'storageID: ' + str(loggedJobs[i].args['storageID']) + '\n' +
           'sourceCodeHash: ' + loggedJobs[i].args['sourceCodeHash'] + '\n' +
           'gasDataTransferIn: ' + str(loggedJobs[i].args['gasDataTransferIn']) + '\n' +
           'gasDataTransferOut: ' + str(loggedJobs[i].args['gasDataTransferOut']) + '\n' +
           'cacheType: ' + str(loggedJobs[i].args['cacheType']))
       
       if loggedJobs[i]['blockNumber'] > int(maxVal): 
          maxVal = loggedJobs[i]['blockNumber']

       jobKey = loggedJobs[i].args['jobKey']
       index  = int(loggedJobs[i].args['index'])
       strCheck,status = lib.runCommand(["bash", lib.EBLOCPATH + "/strCheck.sh", jobKey])
                     
       for attempt in range(10):
           try:
               jobInfo  = getJobInfo(clusterAddress, jobKey, index, eBlocBroker, web3)
               log('core: ' + str(jobInfo['core']))               
           except Exception as e:
               log("Error: jobInfo returns as " + jobInfo, 'red')
           else:
               break
       else:
           runFlag = 1
           break       
       
       userID   = ""
       if runFlag == 1 or jobInfo['core'] == 0: 
          log('Job does not exist', 'red')
          runFlag = 1
       else:
          log('jobOwner/userID: ' + jobInfo['jobOwner'])
          userID    = jobInfo['jobOwner'].lower()
          userExist = isUserExist(userID, eBlocBroker, web3)          

          if jobInfo['status'] == str(lib.job_state_code['COMPLETED']):
             log('Job is already completed.', 'red')
             runFlag = 1
          if jobInfo['status'] == str(lib.job_state_code['REFUNDED']):
             log("Job is refunded.", 'red')
             runFlag = 1
          if runFlag == 0 and not jobInfo['status'] == lib.job_state_code['PENDING']:
             log("Job is already captured and in process or completed.", 'red')
             runFlag = 1
          if 'False' in strCheck:
             log('Filename contains invalid character', 'red')
             runFlag = 1
          if not userExist: 
             log('jobOwner is not registered', 'red')
             runFlag = 1
          else:
             userInfo = getUserInfo(userID, '1', eBlocBroker, web3)
             
          slurmPendingJobCheck() # TODO: if jobs are bombared idle core won't updated
          log('Adding user...', 'green')
          res, status = lib.runCommand(['sudo', 'bash', lib.EBLOCPATH + '/user.sh', userID, lib.PROGRAM_PATH])
          log(res)                    
          userIDmd5 = hashlib.md5(userID.encode('utf-8')).hexdigest()
          
       if runFlag == 1:
          pass
       elif str(loggedJobs[i].args['storageID']) == '0':
          log("New job has been received. IPFS call |" + time.ctime(), "green")
          driverFunc.driverIpfs(loggedJobs[i].args['jobKey'], str(loggedJobs[i].args['index']),
                                    str(loggedJobs[i].args['storageID']), userIDmd5, loggedJobs[i].args['cacheType'],
                                    eBlocBroker, web3)
       elif str(loggedJobs[i].args['storageID']) == '1':
          if oc is None: #TODO: carry to upper functon
              log("Login into owncloud...")
              with open(lib.EBLOCPATH + '/eudatPassword.txt', 'r') as content_file:
                  password = content_file.read().strip()
                   
              oc = owncloud.Client('https://b2drop.eudat.eu/') 
              oc.login(lib.OC_USER_ID, password)  # Unlocks EUDAT account
              password = None
              
          log("New job has been received. EUDAT call |" + time.ctime(), "green")
          driverEudat(loggedJobs[i].args['jobKey'], str(loggedJobs[i].args['index']), userInfo[4],
                      userIDmd5, loggedJobs[i].args['cacheType'],
                      eBlocBroker, web3, oc)
          
       #thread.start_new_thread(driverFunc.driverEudat, (loggedJobs[i].args['jobKey'], str(loggedJobs[i].args['index']))) 
       elif str(loggedJobs[i].args['storageID']) == '2':
          log('New job has been received. IPFS with miniLock call |' + time.ctime(), 'green')
          driverFunc.driverIpfs(loggedJobs[i].args['jobKey'],
                                str(loggedJobs[i].args['index']),
                                str(loggedJobs[i].args['storageID']),
                                userIDmd5,
                                loggedJobs[i].args['cacheType'],
                                eBlocBroker, web3)
          #thread.start_new_thread(driverFunc.driverIpfs, (loggedJobs[i].args['jobKey'], str(loggedJobs[i].args['index']), str(loggedJobs[i].args['storageID']), submittedJob[5]))
       elif str(loggedJobs[i].args['storageID']) == '3':
          log('New job has been received. GitHub call |' + time.ctime(), 'green')
          driverFunc.driverGithub(loggedJobs[i].args['jobKey'], str(loggedJobs[i].args['index']),
                                  str(loggedJobs[i].args['storageID']), userIDmd5,
                                  loggedJobs[i].args['cacheType'], eBlocBroker, web3)          
       elif str(loggedJobs[i].args['storageID']) == '4':
          log("New job has been received. Googe Drive call |" + time.ctime(), 'green')
          driverGdrive(loggedJobs[i].args['jobKey'], str(loggedJobs[i].args['index']), str(loggedJobs[i].args['storageID']),
                       userIDmd5, loggedJobs[i].args['sourceCodeHash'],
                       loggedJobs[i].args['cacheType'], eBlocBroker, web3)
          
    if len(loggedJobs) > 0 and int(maxVal) != 0:
       f_blockReadFrom = open(lib.BLOCK_READ_FROM_FILE, 'w') # Updates the latest read block number
       f_blockReadFrom.write(str(int(maxVal) + 1) + '\n')
       f_blockReadFrom.close()
       blockReadFrom = str(int(maxVal) + 1)

    # If there is no submitted job for the cluster, block start to read from current block number
    if isClusterReceivedJob == 0:
       f_blockReadFrom = open(lib.BLOCK_READ_FROM_FILE, 'w') # Updates the latest read block number
       f_blockReadFrom.write(str(currentBlockNumber) + '\n')
       f_blockReadFrom.close()
       blockReadFrom = str(currentBlockNumber)
