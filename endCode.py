#!/usr/bin/env python

import sys, os, time, lib, base64, glob, getpass, subprocess, json, shutil
from colored import stylize
from colored import fg
import hashlib
from imports import connectEblocBroker
from imports import getWeb3
from os.path import expanduser
sys.path.insert(0, './contractCalls')
from contractCalls.getJobInfo   import getJobInfo
from contractCalls.getUserInfo  import getUserInfo
from contractCalls.receiptCheck import receiptCheck

web3        = getWeb3()
eBlocBroker = connectEblocBroker(web3)
homeDir     = expanduser("~")
   
def log(strIn, color=''):
    if color != '':
        print(stylize(strIn, fg(color))) 
    else:
       print(strIn)
       txFile = open(lib.LOG_PATH + '/endCodeAnalyse/' + globals()['jobKey'] + "_" + globals()['index'] + '.txt', 'a') 
       txFile.write(strIn + "\n")  
       txFile.close() 

def uploadResultToEudat(encodedShareToken, outputFileName):
    ''' cmd: ( https://stackoverflow.com/a/44556541/2402577, https://stackoverflow.com/a/24972004/2402577 )
    curl -X PUT -H \'Content-Type: text/plain\' -H \'Authorization: Basic \'$encodedShareToken\'==\' \
            --data-binary \'@result-\'$clusterID\'-\'$index\'.tar.gz\' https://b2drop.eudat.eu/public.php/webdav/result-$clusterID-$index.tar.gz

    curl --fail -X PUT -H 'Content-Type: text/plain' -H 'Authorization: Basic 'SjQzd05XM2NNcFoybkFLOg'==' --data-binary
    '@0b2fe6dd7d8e080e84f1aa14ad4c9a0f_0.txt' https://b2drop.eudat.eu/public.php/webdav/result.txt
    '''
    p = subprocess.Popen(['curl', '--fail', '-X', 'PUT', '-H', 'Content-Type: text/plain', '-H',
                          'Authorization: Basic ' +  encodedShareToken,
                          '--data-binary',  '@' + outputFileName,
                          'https://b2drop.eudat.eu/public.php/webdav/' + outputFileName],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err =  p.communicate()
    return p, output, err
                  
def runCommand(command, my_env=None):
    if my_env is None:
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else :
        p = subprocess.Popen(command, env=my_env,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
    output, err = p.communicate()      
    if p.returncode != 0:
        err = err.decode('utf-8')
        log(err, 'red')
    return output.strip().decode('utf-8')

def receiptCheckTx(jobKey, index, elapsedRawTime, newHash, storageID, jobID, dataTransferIn, dataTransferSum):
    # cmd: scontrol show job jobID | grep 'EndTime'| grep -o -P '(?<=EndTime=).*(?= )'
    p1 = subprocess.Popen(['scontrol', 'show', 'job', jobID], stdout=subprocess.PIPE)
    #-----------
    p2 = subprocess.Popen(['grep', 'EndTime'], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    #-----------
    p3 = subprocess.Popen(['grep', '-o', '-P', '(?<=EndTime=).*(?= )'], stdin=p2.stdout,stdout=subprocess.PIPE)
    p2.stdout.close()
    date = p3.communicate()[0].decode('utf-8').strip()

    command = ["date", "-d", date, '+\'%s\''] # cmd: date -d 2018-09-09T21:50:51 +"%s"
    endTimeStamp = runCommand(command).replace("\'","")   
    log("endTimeStamp: " + endTimeStamp) 
    
    txHash = receiptCheck(jobKey, index, elapsedRawTime, newHash, storageID, endTimeStamp, dataTransferIn, dataTransferSum, eBlocBroker, web3)
    while txHash == "notconnected" or txHash == "": 
        log("Error: Please run geth on the background.", 'red')
        log(jobKey + ' ' + index + ' ' + elapsedRawTime + ' ' + newHash + ' ' + storageID + ' ' + endTimeStamp) 
        txHash = receiptCheck(jobKey, index, elapsedRawTime, newHash, storageID, endTimeStamp, dataTransferIn, dataTransferSum, eBlocBroker, web3)
        txHash = ''
        time.sleep(5)      
    log("receiptCheck() " + txHash)  
    txFile = open(lib.LOG_PATH + '/transactions/' + lib.CLUSTER_ID + '.txt', 'a') 
    txFile.write(jobKey + "_" + index + "| Tx_hash: " + txHash + "| receiptCheckTxHash\n") 
    txFile.close() 

# Client's loaded files are removed, no need to re-upload them.
def removeSourceCode(resultsFolderPrev):
    # cmd: find . -type f ! -newer $resultsFolder/timestamp.txt  # Client's loaded files are removed, no need to re-upload them.
    command = ['find', '.', '-type', 'f', '!', '-newer', resultsFolderPrev + '/timestamp.txt']
    filesToRemove = runCommand(command)
    if filesToRemove != '' or filesToRemove is not None:
        log('\nFiles to be removed: \n' + filesToRemove + '\n')         
    # cmd: find . -type f ! -newer $resultsFolder/timestamp.txt -delete
    subprocess.run(['find', '.', '-type', 'f', '!', '-newer', resultsFolderPrev + '/timestamp.txt', '-delete'])

def calculateDataTransferOut(outputFileName, pathType):
    dataTransferOut = 0
    if pathType == 'f':
        p1 = subprocess.Popen(['ls', '-ln', outputFileName], stdout=subprocess.PIPE)
        #-----------
        p2 = subprocess.Popen(['awk', '{print $5}'], stdin=p1.stdout, stdout=subprocess.PIPE)
        p1.stdout.close()
        #-----------
        dataTransferOut = p2.communicate()[0].decode('utf-8').strip() # Retunrs downloaded files size in bytes
    elif pathType == 'd':
        p1 = subprocess.Popen(['du', '-sb', outputFileName], stdout=subprocess.PIPE)
        #-----------
        p2 = subprocess.Popen(['awk', '{print $1}'], stdin=p1.stdout, stdout=subprocess.PIPE)
        p1.stdout.close()
        #-----------
        dataTransferOut = p2.communicate()[0].decode('utf-8').strip() # Retunrs downloaded files size in bytes           
    
    dataTransferOut =  int(dataTransferOut) * 0.000001
    log('dataTransferOut=' + str(dataTransferOut) + ' MB | Rounded=' + str(int(dataTransferOut)) + ' MB', 'green')    
    return dataTransferOut

def endCall(jobKey, index, storageID, shareToken, folderName, jobID):
    globals()['jobKey'] = jobKey
    globals()['index']  = index 

    # https://stackoverflow.com/a/5971326/2402577 ... https://stackoverflow.com/a/4453495/2402577
    # my_env = os.environ.copy(); my_env["IPFS_PATH"] = homeDir + "/.ipfs"; print(my_env)
    os.environ["IPFS_PATH"] = homeDir + "/.ipfs"
   
    log('To run again:')
    log('~/eBlocBroker/endCode.py ' + jobKey + ' ' + index + ' ' + storageID + ' ' + shareToken + ' ' + folderName + ' ' + jobID)
    log('')
    log("jobID: " + jobID)   
    if jobKey == index:
        log('JobKey and index are same.', 'red') 
        sys.exit() 
      
    encodedShareToken = '' 
    if shareToken != '-1':      
        encodedShareToken = base64.b64encode((str(shareToken) + ':').encode('utf-8')).decode('utf-8')
      
    log("encodedShareToken: " + encodedShareToken)          
    jobInfo = getJobInfo(lib.CLUSTER_ID, jobKey, index, eBlocBroker, web3)
   
    # while jobInfo == "Connection refused" or jobInfo == "" or jobInfo == "Errno" :
    while not jobInfo or 'BadFunctionCallOutput' in jobInfo:      
        log('jobInfo=' + jobInfo) 
        log('getJobInfo.py ' + ' ' + lib.CLUSTER_ID + ' ' + jobKey + ' ' + index)
        log("Error: Please run geth on the background.", 'red')
        jobInfo = getJobInfo(lib.CLUSTER_ID, jobKey, index, eBlocBroker, web3)
        time.sleep(5)
       
    userID     = jobInfo['jobOwner'].lower()
    userIDAddr = hashlib.md5(userID.encode('utf-8')).hexdigest()  # Convert Ethereum User Address into 32-bits
    userInfo   = getUserInfo(userID, '1', eBlocBroker, web3)

    resultsFolderPrev = lib.PROGRAM_PATH + "/" + userIDAddr + "/" + jobKey + "_" + index 
    resultsFolder     = resultsFolderPrev + '/JOB_TO_RUN'
   
    lib.removeFiles(resultsFolder + '/result-*tar.gz')   
    # cmd: find ./ -size 0 -print0 | xargs -0 rm
    p1 = subprocess.Popen(['find', resultsFolder, '-size', '0', '-print0'], stdout=subprocess.PIPE)
    #-----------
    p2 = subprocess.Popen(['xargs', '-0', '-r', 'rm'], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    #-----------
    p2.communicate() # Remove empty files if exist
    
    # cmd: find ./ -type d -empty -delete | xargs -0 rmdir 
    subprocess.run(['find', resultsFolder, '-type', 'd', '-empty', '-delete'])    
    p1 = subprocess.Popen(['find', resultsFolder, '-type', 'd', '-empty', '-print0'], stdout=subprocess.PIPE)
    #-----------
    p2 = subprocess.Popen(['xargs', '-0', '-r', 'rmdir'], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    #-----------
    p2.communicate() # Remove empty folders if exist      

    log("\nwhoami: "          + getpass.getuser() + ' ' + str(os.getegid())) # whoami
    log("homeDir: "           + homeDir)
    log("pwd: "               + os.getcwd()) # pwd
    log("resultsFolder: "     + resultsFolder) 
    log("jobKey: "            + jobKey) 
    log("index: "             + index) 
    log("storageID: "         + storageID) 
    log("shareToken: "        + shareToken) 
    log("encodedShareToken: " + encodedShareToken)    
    log("folderName: "        + folderName) 
    log("clusterID: "         + lib.CLUSTER_ID) 
    log("userIDAddr: "        + userIDAddr)
    log("received: "          + str(jobInfo['received']))

    dataTransferIn = 0
    if os.path.isfile(resultsFolderPrev + '/dataTransferIn.txt'):
        with open(resultsFolderPrev + '/dataTransferIn.txt') as json_file:
            data = json.load(json_file)
            dataTransferIn = data['dataTransferIn']
    else:
        log('dataTransferIn.txt does not exist...', 'red')
       
    log('dataTransferIn=' + str(dataTransferIn) + ' MB  | Rounded=' + str(int(dataTransferIn)) + ' MB', 'green')  
    if os.path.isfile(resultsFolderPrev + '/modifiedDate.txt'):
        fDate = open(resultsFolderPrev + '/modifiedDate.txt', 'r')
        modifiedDate = fDate.read().rstrip('\n') 
        fDate.close() 
        log(modifiedDate) 

    log("\njobOwner's Info: ")  
    log('{0: <13}'.format('userEmail: ')   + userInfo[1])
    log('{0: <13}'.format('miniLockID: ')  + userInfo[2])
    log('{0: <13}'.format('ipfsAddress: ') + userInfo[3])
    log('{0: <13}'.format('fID: ')         + userInfo[4])
    clientMiniLockID = userInfo[2]       
    log("")    
    if jobInfo['status'] == str(lib.job_state_code['COMPLETED']):
        log('Job is already get paid.', 'red') 
        sys.exit() 

    clientTimeLimit = jobInfo['coreMinuteGas'] 
    log("clientGasMinuteLimit: " + str(clientTimeLimit))  # Clients minuteGas for the job            
    countTry = 0 
    while True: 
        #if countTry > 200: # setJobStatus may deploy late.
        #   sys.exit()
        countTry += 1                  
        log("Waiting for " + str(countTry * 15) + ' seconds to pass...', 'yellow')  
        if jobInfo['status'] == lib.job_state_code['RUNNING']: # It will come here eventually, when setJob() is deployed.
            log("Job has been started.", 'green')  
            break  # Wait until does values updated on the blockchain
      
        if jobInfo['status'] == lib.job_state_code['COMPLETED']: 
            log("Error: Already completed job and its money is received.", 'red')  
            sys.exit()  # Detects an error on the SLURM side

        jobInfo = getJobInfo(lib.CLUSTER_ID, jobKey, index, eBlocBroker, web3)
        lib.web3Exception(jobInfo)      
        time.sleep(15) # Short sleep here so this loop is not keeping CPU busy
      
    log("jobName: " + str(folderName))    
    # cmd: scontrol show job $jobID > $resultsFolder/slurmJobInfo.out
    with open(resultsFolder + '/slurmJobInfo.out', 'w') as stdout:
        subprocess.Popen(['scontrol', 'show', 'job', jobID], stdout=stdout)
        log('Writing into slurmJobInfo.out is done.', 'green')

    command = ['sacct', '-n', '-X', '-j', jobID, '--format=Elapsed'] # cmd: sacct -n -X -j $jobID --format="Elapsed"
    elapsedTime = runCommand(command)
    log("ElapsedTime: " + elapsedTime) 

    elapsedTime    = elapsedTime.split(':') 
    elapsedDay     = "0" 
    elapsedHour    = elapsedTime[0].replace(" ", "") 
    elapsedMinute  = elapsedTime[1].rstrip() 
    elapsedSeconds = elapsedTime[2].rstrip() 

    if "-" in str(elapsedHour):
        elapsedHour = elapsedHour.split('-') 
        elapsedDay  = elapsedHour[0] 
        elapsedHour = elapsedHour[1] 

    elapsedRawTime = int(elapsedDay)* 1440 + int(elapsedHour) * 60 + int(elapsedMinute) + 1 
    log("ElapsedRawTime: " + str(elapsedRawTime))

    if elapsedRawTime > int(clientTimeLimit):
        elapsedRawTime = clientTimeLimit 

    log("finalizedElapsedRawTime: " + str(elapsedRawTime)) 
    log("jobInfo: " + str(jobInfo))
    outputFileName = 'result-' + lib.CLUSTER_ID + '-' + str(index) + '.tar.gz'
   
    # Here we know that job is already completed 
    if str(storageID) == '0' or str(storageID) == '3': # IPFS or GitHub
        for attempt in range(10):
            command = ['ipfs', 'add', '-r', resultsFolder] # Uploaded as folder
            newHash = runCommand(command)
            if newHash=="":
                ''' Approach to upload as .tar.gz. Currently not used.
                removeSourceCode(resultsFolderPrev)
                with open(resultsFolderPrev + '/modifiedDate.txt') as content_file:
                date = content_file.read().strip()
                command = ['tar', '-N', date, '-jcvf', outputFileName] + glob.glob("*")
                log(runCommand(command))
                command = ['ipfs', 'add', resultsFolder + '/result.tar.gz']
                newHash = runCommand(command)
                newHash = newHash.split(' ')[1]
                lib.silentremove(resultsFolder + '/result.tar.gz')
                '''
                log("Generated new hash return empty error. Trying again... Try count: " + str(attempt), 'yellow')
                time.sleep(5) # wait 5 second for next step retry to up-try
            else: # success
	            break
        else: # we failed all the attempts - abort
            sys.exit()
                
        # dataTransferOut = calculateDataTransferOut(resultsFolder, 'd')   
        # cmd: echo newHash | tail -n1 | awk '{print $2}'
        p1 = subprocess.Popen(['echo', newHash], stdout=subprocess.PIPE)
        #-----------
        p2 = subprocess.Popen(['tail', '-n1'], stdin=p1.stdout, stdout=subprocess.PIPE)
        p1.stdout.close()
        #-----------
        p3 = subprocess.Popen(['awk', '{print $2}'], stdin=p2.stdout,stdout=subprocess.PIPE)
        p2.stdout.close()
        #-----------
        newHash = p3.communicate()[0].decode('utf-8').strip()
        log("newHash: " + newHash)

        command = ['ipfs', 'pin', 'add', newHash]
        res = runCommand(command) # pin downloaded ipfs hash
        print(res)

        command = ['ipfs', 'object', 'stat', newHash]
        isIPFSHashExist = runCommand(command) # pin downloaded ipfs hash
        
        for item in isIPFSHashExist.split("\n"):
            if "CumulativeSize" in item:
                dataTransferOut = item.strip().split()[1]
                break
            
        dataTransferOut = int(dataTransferOut) * 0.000001
        log('dataTransferOut=' + str(dataTransferOut) + ' MB | Rounded=' + str(int(dataTransferOut)) + ' MB', 'green')   
    if str(storageID) == '2': # IPFS with miniLock
        os.chdir(resultsFolder) 
        with open(resultsFolderPrev + '/modifiedDate.txt') as content_file:
            date = content_file.read().strip()
            
        command = ['tar', '-N', date, '-jcvf', outputFileName] + glob.glob("*")    
        log(runCommand(command))            
        # cmd: mlck encrypt -f $resultsFolder/result.tar.gz $clientMiniLockID --anonymous --output-file=$resultsFolder/result.tar.gz.minilock
        command = ['mlck', 'encrypt' , '-f', resultsFolder + '/result.tar.gz', clientMiniLockID,
                   '--anonymous', '--output-file=' + resultsFolder + '/result.tar.gz.minilock']
        res = runCommand(command)
        log(res)      
        removeSourceCode(resultsFolderPrev)
        for attempt in range(10):
            command = ['ipfs', 'add', resultsFolder + '/result.tar.gz.minilock']
            newHash = runCommand(command)
            newHash = newHash.split(' ')[1]
            if newHash == "":
                log("Generated new hash return empty error. Trying again... Try count: " + str(attempt), 'yellow')
                time.sleep(5) # wait 5 second for next step retry to up-try
            else: # success
                break
        else: # we failed all the attempts - abort
            sys.exit()
                   
        # dataTransferOut = calculateDataTransferOut(resultsFolder + '/result.tar.gz.minilock', 'f')   
        log("newHash: " + newHash)
        command = ['ipfs', 'pin', 'add', newHash]
        res = runCommand(command)     
        print(res)
        command = ['ipfs', 'object', 'stat', newHash]      
        isIPFSHashExist = runCommand(command)
        for item in isIPFSHashExist.split("\n"):
            if "CumulativeSize" in item:
                dataTransferOut = item.strip().split()[1]
                break
            
        dataTransferOut = int(dataTransferOut) * 0.000001
        log('dataTransferOut=' + str(dataTransferOut) + ' MB | Rounded=' + str(int(dataTransferOut)) + ' MB', 'green')         
    elif str(storageID) == '1': # EUDAT
        log('Entered into Eudat case')
        newHash = '0x00'
        lib.removeFiles(resultsFolder + '/.node-xmlhttprequest*')      
        os.chdir(resultsFolder) 
        removeSourceCode(resultsFolderPrev)      
        # cmd: tar -jcvf result-$clusterID-$index.tar.gz *
        # command = ['tar', '-jcvf', outputFileName] + glob.glob("*")      
        # log(runCommand(command))
        with open(resultsFolderPrev + '/modifiedDate.txt') as content_file:
            date = content_file.read().strip()

        command = ['tar', '-N', date, '-jcvf', outputFileName] + glob.glob("*")   
        log('Files to be archived using tar: \n' + runCommand(command))
        dataTransferOut = calculateDataTransferOut(outputFileName, 'f')      
        for attempt in range(5):
            p, output, err = uploadResultToEudat(encodedShareToken, outputFileName)
            output = output.strip().decode('utf-8')
            err = err.decode('utf-8')      
            if p.returncode != 0 or '<d:error' in output:
                log('Error: EUDAT repository did not successfully loaded.', 'red')
                log("curl failed %d %s . %s" % (p.returncode, err.decode('utf-8'), output))
                time.sleep(1) # wait 1 second for next step retry to upload                
            else: # success on upload                
                break    
        else: # we failed all the attempts - abort            
            sys.exit()         
    elif str(storageID) == '4': #GDRIVE
        newHash = '0x00'
        #cmd: gdrive info $jobKey -c $GDRIVE_METADATA # stored for both pipes otherwise its read and lost
        gdriveInfo, status = lib.subprocessCallAttempt([lib.GDRIVE, 'info', jobKey, '-c', lib.GDRIVE_METADATA], 500, 1)
        if not status: return False
   
        mimeType = lib.getMimeType(gdriveInfo)            
        log('mimeType=' + str(mimeType))                
        os.chdir(resultsFolder) 
        #if 'folder' in mimeType: # Received job is in folder format
        removeSourceCode(resultsFolderPrev)
        with open(resultsFolderPrev + '/modifiedDate.txt', 'r') as content_file:
            date = content_file.read().rstrip()
            
        command = ['tar', '-N', date, '-jcvf', outputFileName] + glob.glob("*")    
        log(runCommand(command))            
        time.sleep(0.25) 
        dataTransferOut = calculateDataTransferOut(outputFileName, 'f')
        if 'folder' in mimeType: # Received job is in folder format
            log('mimeType: folder')                        
            # cmd: $GDRIVE upload --parent $jobKey result-$clusterID-$index.tar.gz -c $GDRIVE_METADATA
            command = [lib.GDRIVE, 'upload', '--parent', jobKey, outputFileName, '-c', lib.GDRIVE_METADATA]
            res, status = lib.subprocessCallAttempt(command, 500)            
            log(res)         
        elif 'gzip' in mimeType: # Received job is in folder tar.gz
            log('mimeType: tar.gz')
            # cmd: $GDRIVE update $jobKey result-$clusterID-$index.tar.gz -c $GDRIVE_METADATA
            command = [lib.GDRIVE, 'update', jobKey, outputFileName, '-c', lib.GDRIVE_METADATA]
            res, status = lib.subprocessCallAttempt(command, 500)            
            log(res)         
        elif '/zip' in mimeType: # Received job is in zip format
            log('mimeType: zip')
            # cmd: $GDRIVE update $jobKey result-$clusterID-$index.tar.gz -c $GDRIVE_METADATA
            command = [lib.GDRIVE, 'update', jobKey, outputFileName, '-c', lib.GDRIVE_METADATA]
            res, status = lib.subprocessCallAttempt(command, 500)            
            log(res)         
        else:
            log('Error: Files could not be uploaded', 'red')
            sys.exit()
         
    dataTransferSum = dataTransferIn + dataTransferOut   
    log('dataTransferSum=' + str(dataTransferSum) + ' MB | Rounded=' + str(int(dataTransferOut)) + ' MB', 'green')
    receiptCheckTx(jobKey, index, elapsedRawTime, newHash, storageID, jobID, dataTransferIn, dataTransferSum)
    log('DONE.', 'green')
    '''
    # Removed downloaded code from local since it is not needed anymore
    if os.path.isdir(resultsFolderPrev):
    shutil.rmtree(resultsFolderPrev) # deletes a directory and all its contents.
    '''
if __name__ == '__main__':
    jobKey      = sys.argv[1] 
    index       = sys.argv[2] 
    storageID   = sys.argv[3] 
    shareToken  = sys.argv[4] 
    folderName  = sys.argv[5] 
    jobID       = sys.argv[6] 

    endCall(jobKey, index, storageID, shareToken, folderName, jobID)
