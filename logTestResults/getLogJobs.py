#!/usr/bin/env python3

import os
import subprocess
import sys
from os.path import expanduser

from dotenv import load_dotenv

import lib
from contractCalls.get_job_info import get_job_info
from imports import connect

home = expanduser("~")
eBlocBroker, w3 = connect()
ipfsFlag = 0


def getLogJobs(providerAddress, fromBlock):
    print("providerAddress:" + providerAddress + "\n")
    myFilter = eBlocBroker.events.LogReceipt.createFilter(
        fromBlock=int(fromBlock), argument_filters={"providerAddress": str(providerAddress)}
    )
    loggedJobs = myFilter.get_all_entries()

    receiptReturned = {}

    for i in range(0, len(loggedJobs)):
        providerAddress = loggedJobs[i].args["providerAddress"]
        jobKey = loggedJobs[i].args["jobKey"]
        index = loggedJobs[i].args["index"]
        returned = loggedJobs[i].args["returned"]
        receiptReturned[f"{providerAddress}_{jobKey}_{index}"] = returned

    myFilter = eBlocBroker.events.LogJob.createFilter(
        fromBlock=int(fromBlock), argument_filters={"providerAddress": str(providerAddress)}
    )
    loggedJobs = myFilter.get_all_entries()
    sum_ = 0
    completedCounter = 0
    for idx, logged_job in enumerate(loggedJobs, start=1):
        providerAddress = logged_job.args["providerAddress"]
        jobKey = logged_job.args["jobKey"]
        index = logged_job.args["index"]
        _blockNumber = logged_job["blockNumber"]
        # print(loggedJobs[i])
        # print(loggedJobs[i].args['jobKey'])
        jobInfo = get_job_info(providerAddress, jobKey, index, _blockNumber)
        # print('received: ' +  )
        returned = 0
        key = f"{providerAddress}_{jobKey}_{index}"
        if key in receiptReturned:
            returned = receiptReturned[key]
            # print('returned:' + str(receiptReturned[key]))
        # else:
        #    print('returned:0')

        gained = 0
        if lib.inv_job_state_code[int(jobInfo["status"])] == "COMPLETED":
            # print('gained: ' + str(jobInfo['received'] - returned))
            gained = jobInfo["received"] - returned
            sum_ += gained
            completedCounter += 1
        # else:
        #   print('gained:0')

        print(
            str(idx)
            + " | "
            + loggedJobs[i].args["jobKey"]
            + " "
            + str(loggedJobs[i].args["index"])
            + " "
            + lib.inv_job_state_code[int(jobInfo["status"])]
            + " "
            + str(jobInfo["received"])
            + " "
            + str(returned)
            + " "
            + str(gained)
        )

        if ipfsFlag == 1 and lib.inv_job_state_code[int(jobInfo["status"])] == "COMPLETED":
            subprocess.run(
                ["ipfs", "get", loggedJobs[i].args["jobKey"], "--output=ipfsHashes/" + loggedJobs[i].args["jobKey"]]
            )

    print("TOTAL_GAINED: " + str(sum_))
    print(str(completedCounter) + "/" + str(idx - 1))


if __name__ == "__main__":
    if len(sys.argv) == 3:
        providerAddress = str(sys.argv[1])
        fromBlock = int(sys.argv[2])
    else:
        load_dotenv(os.path.join(home + "/.eBlocBroker", ".env"))  # Load .env from the given path
        providerAddress = os.getenv("PROVIDER_ID")
        fromBlock = 2215127

    print(fromBlock)
    getLogJobs(providerAddress, fromBlock)
