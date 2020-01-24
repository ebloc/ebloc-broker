#!/usr/bin/env python3

import os, lib, sys
from imports import connectEblocBroker, getWeb3
from contractCalls.get_job_info import get_job_info

w3 = getWeb3()
eBlocBroker = connectEblocBroker(w3)
# Paths----------------------------------
eblocPath = lib.EBLOCPATH
fname = lib.LOG_PATH + "/queuedJobs.txt"
# ---------------------------------------
sum1 = 0
counter = 1
with open(fname, "r") as ins:
    array = []
    for line in ins:
        # print(line.rstrip('\n'))
        # array.append(line)

        res = line.split(" ")

        providerAddress = res[1]
        jobKey = res[2]
        index = res[3]

        sum1 += int(res[7]) - int(res[8])
        jobInfo = get_job_info(providerAddress, jobKey, index, None, eBlocBroker, w3)

        print(
            str(counter)
            + " "
            + res[1]
            + " "
            + res[2]
            + " "
            + res[3]
            + "|"
            + "{0: <16}".format("status:")
            + lib.job_state_code[str(jobInfo["status"])]
            + " "
            + "{0: <16}".format('core"')
            + str(jobInfo["core"])
            + " "
            + "{0: <16}".format('startTime"')
            + str(jobInfo["startTime"])
            + " "
            + "{0: <16}".format("received:")
            + str(jobInfo["received"])
            + " "
            + "{0: <16}".format("coreMinPrice:")
            + str(jobInfo["coreMinPrice"])
            + " "
            + "{0: <16}".format("memoryMinPrice:")
            + str(jobInfo["memoryMinPrice"])
            + " "
            + "{0: <16}".format("coreMinuteGas:")
            + str(jobInfo["coreMinuteGas"])
            + " "
            + "{0: <16}".format("jobInfoOwner:")
            + jobInfo["jobOwner"]
        )
        counter += 1

print(counter)
print("GAINED: " + str(sum1))
