#!/usr/bin/env python3

import pwd, os, sys, binascii, pprint, owncloud, json
import time, subprocess, string, driverFunc, _thread
import hashlib
import sys, signal

from subprocess import call
from colored import stylize
from colored import fg


from imports import connect

from lib import isSlurmOn, log, terminate, executeShellCommand
from lib import WHOAMI, EBLOCPATH, PROVIDER_ID, RPC_PORT, HOME, EUDAT_USE, IPFS_USE, BLOCK_READ_FROM_FILE, CacheType, StorageID, job_state_code, PROGRAM_PATH

from driverEudat  import driverEudat
from driverGdrive import driverGdrive

from contractCalls.getProviderReceivedAmount import getProviderReceivedAmount
from contractCalls.getDeployedBlockNumber    import getDeployedBlockNumber
from contractCalls.isContractExists          import isContractExists
from contractCalls.isProviderExists          import isProviderExists
from contractCalls.blockNumber               import blockNumber
from contractCalls.getJobInfo                import getJobInfo
from contractCalls.isRequesterExists         import isRequesterExists
from contractCalls.getRequesterInfo          import getRequesterInfo
from contractCalls.isWeb3Connected           import isWeb3Connected
from contractCalls.LogJob                    import runLogJob

eBlocBroker, w3 = connect()
if eBlocBroker is None or w3 is None:
    sys.exit()

driverCancelProcess   = None
driverReceiverProcess = None
oc                    = None
my_env = os.environ.copy()

# Dummy sudo command to get the password when session starts
subprocess.run(['sudo', 'printf', '']) 

"""Runs driverCancel daemon on the background."""
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

"""Runs driverReceiver daemon on the background."""
def runWhisperStateReceiver():
    if not os.path.isfile(HOME + '/.eBlocBroker/whisperInfo.txt'):
        # First time running:
        log('Please first run: scripts/whisperInitialize.py')
        terminate()
    else:
        with open(HOME + '/.eBlocBroker/whisperInfo.txt') as json_file:
            data = json.load(json_file)
            
        kId = data['kId']
        publicKey = data['publicKey']
        if not w3.geth.shh.hasKeyPair(kId):
            log("Error: Whisper node's private key of a key pair did not match with the given ID", 'red')
            log('Please first run: scripts/whisperInitialize.py', 'red')
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

def idleCoreNumber(printFlag=1):    
    status, coreInfo = executeShellCommand(['sinfo', '-h', '-o%C']) # cmd: sinfo -h -o%C
    coreInfo = coreInfo.split('/')    
    if len(coreInfo) != 0:
       idleCore = coreInfo[1]
       if printFlag == 1:
          log('AllocatedCores=' + coreInfo[0] + '| IdleCores='          + coreInfo[1] +
              '| OtherCores='   + coreInfo[2] + '| TotalNumberOfCores=' + coreInfo[3], 'blue')
    else:
       log('sinfo return emptry string.', 'red')
       idleCore = None
       
    return idleCore

""" If there is no idle cores, waits for idle cores to be emerged. """
def slurmPendingJobCheck():
    idleCore  = idleCoreNumber()       
    printFlag = 0    
    while idleCore is None:
       if printFlag == 0:
          log('Waiting running jobs to be completed...', 'blue')
          printFlag = 1
          
       time.sleep(10)
       idleCore = idleCoreNumber(0)

# Checks whether geth runs on the background
def isGethOn():
   # cmd: ps aux | grep [g]eth | grep '8545' | wc -l
   p1 = subprocess.Popen(['ps', 'aux'], stdout=subprocess.PIPE)
   p2 = subprocess.Popen(['grep', '[g]eth'], stdin=p1.stdout, stdout=subprocess.PIPE)
   p1.stdout.close()
   p3 = subprocess.Popen(['grep', str(RPC_PORT)], stdin=p2.stdout,stdout=subprocess.PIPE)
   p2.stdout.close()
   p4 = subprocess.Popen(['wc', '-l'], stdin=p3.stdout,stdout=subprocess.PIPE)
   p3.stdout.close()
   out = p4.communicate()[0].decode('utf-8').strip()
   
   if int(out) == 0:
      log("Geth is not running on the background.", 'red')
      terminate()      

# Checks: does Driver.py runs on the background
def isDriverOn(): 
   # cmd: ps aux | grep \'[D]river.py\' | grep \'python\' | wc -l
   p1 = subprocess.Popen(['ps', 'aux'], stdout=subprocess.PIPE)
   p2 = subprocess.Popen(['grep', '[D]river.py'], stdin=p1.stdout, stdout=subprocess.PIPE)
   p1.stdout.close()
   p3 = subprocess.Popen(['grep', 'python'], stdin=p2.stdout,stdout=subprocess.PIPE)
   p2.stdout.close()
   p4 = subprocess.Popen(['wc', '-l'], stdin=p3.stdout,stdout=subprocess.PIPE)
   p3.stdout.close()
   out = p4.communicate()[0].decode('utf-8').strip()
   
   if int(out) > 1:
      log("Driver is already running.", 'green')

def eudatLoginAndCheck():
    log("Login into owncloud... ", 'blue', False)
    global oc
    if OC_USER is None or OC_USER == "":
        log("OC_USER is not set in .env", "red")
        sys.exit()
        
    with open(LOG_PATH + '/eudatPassword.txt', 'r') as content_file:
        password = content_file.read().strip()
        
    oc = owncloud.Client('https://b2drop.eudat.eu/') 
    oc.login(OC_USER, password)  # Unlocks EUDAT account    
    password = None
    try:
        oc.list('.')
        log("SUCCESS", 'green')
    except subprocess.CalledProcessError as e:
        log("FAILED. " + e.output.decode('utf-8').strip(), 'red')        
        sys.exit()
        
# Startup functions are called
def startup():    
    isDriverOn()
    isSlurmOn()
    isGethOn()
    # runDriverCancel()    
    runWhisperStateReceiver()
    if EUDAT_USE:
        eudatLoginAndCheck()

def checkPrograms():
    status, result = executeShellCommand(['gdrive', 'version'])
    if not status:
        log('Please install gdrive or check its path', 'red')
        sys.exit()

checkPrograms()

yes = set(['yes', 'y', 'ye'])
no  = set(['no' , 'n'])
if WHOAMI == '' or EBLOCPATH == '' or PROVIDER_ID == '': 
   print(stylize('Please run:  ./initialize.sh \n', fg('red')))
   terminate()

log('=' * int(int(columns) / 2 - 12) + ' provider session starts ' + '=' * int(int(columns) / 2 - 12), 'green')

startup()
isContractExists = isContractExists(w3)
if not isContractExists:
   log("Please check that you are using eBlocPOA blockchain", 'red')
   terminate()

log('isWeb3Connected=' + str(isWeb3Connected(w3)))
log('rootdir: ' + os.getcwd())
contract = json.loads(open('contractCalls/contract.json').read())    
contractAddress = contract['address']
log('{0: <20}'.format('contractAddress:') + '"' + contractAddress + '"', "yellow")

if IPFS_USE:
    isIpfsOn()

provider = PROVIDER_ID
isProviderExists = isProviderExists(provider, eBlocBroker, w3)
if not isProviderExists:
   print(stylize("Error: Your Ethereum address '" + provider + "' \n"
                 "does not match with any provider in eBlocBroker. Please register your \n" 
                 "provider using your Ethereum Address in to the eBlocBroker. You can \n"   
                 "use 'contractCalls/registerProvider.py' script to register your provider.",
                 fg('red')))
   terminate()

deployedBlockNumber   = str(getDeployedBlockNumber(eBlocBroker))
blockReadFromContract = '0'
log('{0: <20}'.format('providerAddress:') + '"'+ provider + '"', 'yellow')
if not os.path.isfile(BLOCK_READ_FROM_FILE): 
   f = open(BLOCK_READ_FROM_FILE, 'w')
   f.write(deployedBlockNumber + "\n")
   f.close()

f = open(BLOCK_READ_FROM_FILE, 'r')
blockReadFromLocal = f.read().rstrip('\n')
f.close()

if not blockReadFromLocal.isdigit(): 
   log("Error: BLOCK_READ_FROM_FILE is empty or contains and invalid value")
   log("#> Would you like to read from contract's deployed block number? y/n")   
   while True: 
      choice = input().lower()
      if choice in yes:
         blockReadFromLocal = deployedBlockNumber
         f = open(BLOCK_READ_FROM_FILE, 'w')
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

providerGainedAmountInit = getProviderReceivedAmount(provider, eBlocBroker, w3)
log('{0: <20}'.format('deployedBlockNumber=') + deployedBlockNumber + " | providerGainedWei=" + providerGainedAmountInit)

while True:
    if "Error" in blockReadFrom:
       log(blockReadFrom)
       terminate()

    providerGainedAmount = getProviderReceivedAmount(provider, eBlocBroker, w3) 
    status, squeueStatus = executeShellCommand(['squeue'])    
    if "squeue: error:" in str(squeueStatus):
       log("SLURM is not running on the background, please run: sudo ./runSlurm.sh. \n")
       log(squeueStatus)
       terminate()
       
    idleCore = idleCoreNumber()    
    log("Current Slurm Running jobs status: \n" + squeueStatus)
    log('-' * int(columns), "green")
    if 'notconnected' != providerGainedAmount:
       log("Current Time: " + time.ctime() + " | providerGainedWei=" + str(int(providerGainedAmount) - int(providerGainedAmountInit)))
       
    log("Waiting new job to come since block number=" + blockReadFrom, 'green')    
    currentBlockNumber = blockNumber() 
    log("Waiting for new block to increment by one.")
    log("Current BlockNumber=" + currentBlockNumber  + "| sync from block number=" + blockReadFrom)
    print('isWeb3Connected=' + str(isWeb3Connected(w3)))
    while int(currentBlockNumber) < int(blockReadFrom):
       time.sleep(1)
       currentBlockNumber = blockNumber(w3)

    log("Passed incremented block number... Continue to wait from block number=" + blockReadFrom)   
    blockReadFrom = str(blockReadFrom) # Starting reading event's location has been updated
    # blockReadFrom = '3082590' # used for test purposes
    slurmPendingJobCheck()
    loggedJobs = runLogJob(blockReadFrom, provider, eBlocBroker)        
    maxVal                = 0
    isProviderReceivedJob = False
    counter               = 0
    shouldAlreadyCached   = {}    
    
    for i in range(0, len(loggedJobs)):               
       passFlag = False
       isProviderReceivedJob = True
       log(str(counter) + ' ' + '-' * (int(columns) - 2), "green")
       counter += 1       
       # sourceCodeHash = binascii.hexlify(loggedJobs[i].args['sourceCodeHash'][0]).decode("utf-8")[0:32]       
       jobKey      = loggedJobs[i].args['jobKey']
       index       = int(loggedJobs[i].args['index'])
       storageID   = loggedJobs[i].args['storageID']
       blockNumber = loggedJobs[i]['blockNumber']
       
       log('blockNumber=' + str(blockNumber)  + '\n' +
           'provider='    + loggedJobs[i].args['provider']     + '\n' +
           'jobKey='      + jobKey     + '\n' +
           'index='       + str(index) + '\n' +
           'cacheType='   + CacheType(loggedJobs[i].args['cacheType']).name + '\n' +
           'received='    + str(loggedJobs[i].args['received']))
                     
       receivedBlock = []
       cacheDuration = []       

       for j in range(0, len(loggedJobs[i].args['sourceCodeHash'])):
           if storageID == StorageID.IPFS.value or storageID == StorageID.IPFS_MINILOCK.value:
               sourceCodeHash_bytes = loggedJobs[i].args['sourceCodeHash'][j]
               sourceCodeHash = convertBytes32ToIpfs(sourceCodeHash_bytes)
           else:               
               sourceCodeHash_bytes = loggedJobs[i].args['sourceCodeHash'][j]
               sourceCodeHash = w3.toText(sourceCodeHash_bytes)

           _receivedBlock, _cacheDuration = eBlocBroker.functions.getJobStorageTime(w3.toChecksumAddress(provider), sourceCodeHash_bytes).call()
           receivedBlock.append(_receivedBlock)
           cacheDuration.append(_cacheDuration)

           if _receivedBlock + _cacheDuration < blockNumber: # // Remaining time to cache is 0               
               shouldAlreadyCached[sourceCodeHash] = False
           else: # Cache is requested for the sourceCodeHash
               if _receivedBlock < blockNumber:                   
                   shouldAlreadyCached[sourceCodeHash] = True
               elif _receivedBlock == blockNumber:                   
                   if (blockNumber, sourceCodeHash) in shouldAlreadyCached:
                       shouldAlreadyCached[sourceCodeHash] = True
                   else:
                       shouldAlreadyCached[sourceCodeHash] = False # For the first job should be False since it is requested for cache for the first time
                       
           log('sourceCodeHash[' + str(j) + ']=' + sourceCodeHash + ' | receivedBlock=' + str(_receivedBlock) + ' | cacheDuration(Hour)=' + str(_cacheDuration) + '| storageID[' + str(j) + ']=' + StorageID(storageID[j]).name + '| shouldAlreadyCached=' + str(shouldAlreadyCached[sourceCodeHash]))
           
       if loggedJobs[i].args['storageID'] == StorageID.IPFS or loggedJobs[i].args['storageID'] == StorageID.IPFS_MINILOCK: 
           sourceCodeHash = convertBytes32ToIpfs(loggedJobs[i].args['sourceCodeHash'])
           if sourceCodeHash != loggedJobs[i].args['jobKey']:
               log('IPFS hash does not match with the given sourceCodeHash.', 'red')
               passFlag = True

       if loggedJobs[i]['blockNumber'] > int(maxVal): 
          maxVal = loggedJobs[i]['blockNumber']

       if loggedJobs[i].args['storageID'] == StorageID.GITHUB.value:
           status, strCheck = executeShellCommand(['bash', EBLOCPATH + '/strCheck.sh', jobKey.replace('=', '', 1)])           
       else:
           status, strCheck = executeShellCommand(['bash', EBLOCPATH + '/strCheck.sh', jobKey])
           
       jobInfo = []
       jobID = 0
       for attempt in range(10):           
           status, _jobInfo = getJobInfo(provider, jobKey, index, jobID, eBlocBroker, w3)
           _jobInfo.update( {'receivedBlock' : receivedBlock} )
           _jobInfo.update( {'cacheDuration' : cacheDuration} )               
           pprint.pprint(_jobInfo)
           jobInfo.append(_jobInfo)               
           if status: 
               break
           else:
               log("Error: " + jobInfo, 'red')
               time.sleep(1)
       else:
           passFlag = True
           break       
       
       jobID = 1
       while not passFlag:
           _jobInfo = eBlocBroker.functions.getJobInfo(w3.toChecksumAddress(provider), jobKey, int(index), int(jobID)).call()
           if _jobInfo[1] == 0: # compares job core value 
               break
           else:
               _jobInfo = getJobInfo(provider, jobKey, index, jobID, eBlocBroker, w3)               
               if _jobInfo != None:
                   jobInfo.append(_jobInfo) # Adding jobs if workflow exist
                   jobID += 1
        
       requesterID   = ""
       if passFlag or jobInfo[0]['core'] == 0: 
           log('Requested job does not exist', 'red')
           passFlag = True
       else:
          log('jobOwner/requesterID: ' + jobInfo[0]['jobOwner'])
          requesterID    = jobInfo[0]['jobOwner'].lower()
          requesterExist = isRequesterExists(requesterID, eBlocBroker, w3)          
          if jobInfo[0]['stateCode'] == str(job_state_code['COMPLETED']):
             log('Job is already completed.', 'red')
             passFlag = True
          if jobInfo[0]['stateCode'] == str(job_state_code['REFUNDED']):
             log("Job is refunded.", 'red')
             passFlag = True
          if not passFlag and not jobInfo[0]['stateCode'] == job_state_code['SUBMITTED']:
              log('Job is already captured. It is in process or completed.', 'red')
              passFlag = True
          if 'False' in strCheck:
             log('Filename contains invalid character', 'red')
             passFlag = True
          if not requesterExist: 
             log('jobOwner is not registered', 'red')
             passFlag = True
          else:
             status, requesterInfo = getRequesterInfo(requesterID, eBlocBroker, w3)             

       if not passFlag: 
           log('Adding user...', 'green')
           status, res = executeShellCommand(['sudo', 'bash', EBLOCPATH + '/user.sh', requesterID, PROGRAM_PATH])
           log(res)                    
           requesterIDmd5 = hashlib.md5(requesterID.encode('utf-8')).hexdigest()          
           slurmPendingJobCheck()
           _storageID = loggedJobs[i].args['storageID'][0]
           if _storageID == StorageID.IPFS.value:
               log('New job has been received. IPFS call |' + time.ctime(), 'green')          
               driverFunc.driverIpfs(loggedJobs[i], jobInfo, requesterIDmd5, eBlocBroker, w3)
           elif _storageID == StorageID.EUDAT.value:
               log('New job has been received. EUDAT call |' + time.ctime(), 'green')
               if oc is None:
                   eudatLoginAndCheck()

               driverEudat(loggedJobs[i], jobInfo, requesterIDmd5, eBlocBroker, w3, oc)
               # thread.start_new_thread(driverFunc.driverEudat, (loggedJobs[i], jobInfo, requesterIDmd5))
           elif _storageID == StorageID.IPFS_MINILOCK.value:
               log('New job has been received. IPFS with miniLock call |' + time.ctime(), 'green')
               driverFunc.driverIpfs(loggedJobs[i], jobInfo, requesterIDmd5, eBlocBroker, w3)
           elif _storageID == StorageID.GITHUB.value:
               log('New job has been received. GitHub call |' + time.ctime(), 'green')
               driverFunc.driverGithub(loggedJobs[i], jobInfo, requesterIDmd5, eBlocBroker, w3)
           elif _storageID == StorageID.GDRIVE.value:
               log('New job has been received. Googe Drive call |' + time.ctime(), 'green')
               driverGdrive(loggedJobs[i], jobInfo, requesterIDmd5, shouldAlreadyCached, eBlocBroker, w3)

    time.sleep(1)       
    if len(loggedJobs) > 0 and int(maxVal) != 0:
       f_blockReadFrom = open(BLOCK_READ_FROM_FILE, 'w') # Updates the latest read block number
       blockReadFrom = str(int(maxVal) + 1)
       f_blockReadFrom.write(blockReadFrom + '\n')
       f_blockReadFrom.close()       

    # If there is no submitted job for the provider, block start to read from current block number
    if not isProviderReceivedJob:
       f_blockReadFrom = open(BLOCK_READ_FROM_FILE, 'w') # Updates the latest read block number
       f_blockReadFrom.write(str(currentBlockNumber) + '\n')
       f_blockReadFrom.close()
       blockReadFrom = str(currentBlockNumber)
