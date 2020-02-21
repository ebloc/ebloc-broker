#!/usr/bin/env python3

import lib
from contractCalls.get_job_info import get_job_info
from imports import connect

eBlocBroker, w3 = connect()

eblocPath = lib.EBLOCPATH
fname = f"{lib.LOG_PATH}/queuedJobs.txt"

sum1 = 0
with open(fname, "r") as ins:
    array = []
    for idx, line in enumerate(ins, start=1):
        # print(line.rstrip('\n'))
        # array.append(line)

        res = line.split(" ")

        providerAddress = res[1]
        jobKey = res[2]
        index = res[3]

        sum1 += int(res[7]) - int(res[8])
        jobInfo = get_job_info(providerAddress, jobKey, index, None)

        print(
            str(idx)
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

print(idx)
print("GAINED: " + str(sum1))
