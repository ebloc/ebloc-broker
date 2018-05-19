#!/usr/bin/env python

import sys, os, constants, _thread

cancelledJobsReadFromPath = constants.CANCEL_JOBS_READ_FROM_FILE;
os.environ['cancelledJobsReadFromPath'] = cancelledJobsReadFromPath;

contractCallPath               = constants.EBLOCPATH + '/contractCalls';
os.environ['contractCallPath'] = contractCallPath;

f = open(constants.CANCEL_BLOCK_READ_FROM_FILE, 'r')
cancelBlockReadFromLocal = f.read().rstrip('\n');
f.close();

if not cancelBlockReadFromLocal.isdigit():
    cancelBlockReadFromLocal = os.popen('$contractCallPath/getDeployedBlockNumber.py').read().rstrip('\n');
    os.environ['cancelBlockReadFromLocal'] = cancelBlockReadFromLocal;
else:
    os.environ['cancelBlockReadFromLocal'] = cancelBlockReadFromLocal;

print('Waiting cancelled jobs from :' + cancelBlockReadFromLocal)

maxVal               = 0;       
while True: #{
    constants.contractCall('eBlocBroker.LogCancelRefund($cancelBlockReadFromLocal, \'$cancelledJobsReadFromPath\')'); # Waits here until new job cancelled into the cluster

    if os.path.isfile(cancelledJobsReadFromPath): #{ Waits until generated file on log is completed       
        cancelledJobs = set() # holds lines already seen
        for line in open(cancelledJobsReadFromPath, "r"):
            if line not in cancelledJobs: # not a duplicate
                cancelledJobs.add(line)

    cancelledJobs= sorted(cancelledJobs);
    for e in cancelledJobs: #{
        cancelledJob = e.rstrip('\n').split(' ');
        os.environ['jobKey'] = cancelledJob[2];
        os.environ['index']  = cancelledJob[3];        
        print(cancelledJob[0] + ' ' + cancelledJob[1] + ' ' + cancelledJob[2] + ' ' + cancelledJob[3]  )

        if int(cancelledJob[0]) > int(maxVal):
            maxVal = cancelledJob[0]

        jobName = os.popen('echo ~/.eBlocBroker/ipfsHashes/$jobKey\_$index/JOB_TO_RUN/$jobKey\*$index*sh | xargs -n 1 basename').read()
        os.environ['jobName']  = jobName;        
        res = os.popen('sacct --name $jobName | tail -n1 | awk \'{print $1}\'').read().rstrip('\n');
        
        if res.isdigit():
            print('JobID: ' + res + ' is cancelled.')
            os.popen('scancel ' + res).read();        
        
        #}

    if int(maxVal) != 0: #{ 
        f_blockReadFrom = open(constants.CANCEL_BLOCK_READ_FROM_FILE, 'w'); # Updates the latest read block number      
        f_blockReadFrom.write(str(int(maxVal) + 1) + '\n'); 
        f_blockReadFrom.close();
        cancelBlockReadFromLocal = str(int(maxVal) + 1);
        os.environ['cancelBlockReadFromLocal'] = cancelBlockReadFromLocal;
        print('Waiting cancelled jobs from :' + cancelBlockReadFromLocal)
    #}
    else:
        currentBlockNumber = os.popen('$contractCallPath/blockNumber.py').read().rstrip('\n')
        
        f_blockReadFrom = open(constants.CANCEL_BLOCK_READ_FROM_FILE, 'w'); # Updates the latest read block number      
        f_blockReadFrom.write(str(currentBlockNumber) + '\n'); 
        f_blockReadFrom.close();
        os.environ['cancelBlockReadFromLocal'] = currentBlockNumber;
        print('Waiting cancelled jobs from :' + currentBlockNumber)
#}
