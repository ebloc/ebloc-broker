#!/usr/bin/env python

import os, lib, sys
from imports import connectEblocBroker
from imports import getWeb3

sys.path.insert(0, './contractCalls')
from contractCalls.getJobInfo import getJobInfo

web3        = getWeb3()
eBlocBroker = connectEblocBroker(web3)
# Paths---------
eblocPath        = lib.EBLOCPATH 
fname = lib.LOG_PATH + '/queuedJobs.txt' 
# ---------------
sum1=0 
counter = 1 
with open(fname, "r") as ins: #{
    array = []
    for line in ins:
        #print(line.rstrip('\n'))
        #array.append(line) 

        res=line.split(' ')

        clusterAddress = res[1]
        jobKey         = res[2] 
        index          = res[3] 

        sum1 += int(res[7]) - int(res[8])
        jobInfo = getJobInfo(clusterAddress, jobKey, index, eBlocBroker, web3)
        print(str(counter) + " " + res[1] + " " + res[2] + " " + res[3] + " | " + lib.job_state_code[jobInfo[0]] +
              "," + jobInfo[1] + "," + jobInfo[2] + "," + jobInfo[3] + "," + jobInfo[4] + "," + jobInfo[5]) 
        counter += 1
#}
print(counter)            
print("GAINED: " + str(sum1)) 
