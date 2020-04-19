#!/usr/bin/env python3

import subprocess
import sys

from config import env
from contractCalls.get_job_info import get_job_info
from imports import connect
from lib import inv_job_state_code

eBlocBroker, w3 = connect()
ipfsFlag = 0


def getLogJobs(provider_address, fromBlock):
    print("provider_address:" + provider_address + "\n")
    myFilter = eBlocBroker.events.LogReceipt.createFilter(
        fromBlock=int(fromBlock), argument_filters={"provider_address": str(provider_address)},
    )
    logged_jobs = myFilter.get_all_entries()

    receiptReturned = {}

    for i in range(0, len(logged_jobs)):
        provider_address = logged_jobs[i].args["provider_address"]
        jobKey = logged_jobs[i].args["jobKey"]
        index = logged_jobs[i].args["index"]
        returned = logged_jobs[i].args["returned"]
        receiptReturned[f"{provider_address}_{jobKey}_{index}"] = returned

    myFilter = eBlocBroker.events.LogJob.createFilter(
        fromBlock=int(fromBlock), argument_filters={"provider_address": str(provider_address)},
    )
    logged_jobs = myFilter.get_all_entries()
    _sum = 0
    completedCounter = 0
    for idx, logged_job in enumerate(logged_jobs, start=1):
        provider_address = logged_job.args["provider_address"]
        jobKey = logged_job.args["jobKey"]
        index = logged_job.args["index"]
        _blockNumber = logged_job["blockNumber"]
        # print(logged_jobs[i])
        # print(logged_jobs[i].args['jobKey'])
        jobInfo = get_job_info(provider_address, jobKey, index, _blockNumber)
        # print('received: ' +  )
        returned = 0
        key = f"{provider_address}_{jobKey}_{index}"
        if key in receiptReturned:
            returned = receiptReturned[key]
            # print('returned:' + str(receiptReturned[key]))
        # else:
        #    print('returned:0')

        gained = 0
        if inv_job_state_code[int(jobInfo["status"])] == "COMPLETED":
            # print('gained: ' + str(jobInfo['received'] - returned))
            gained = jobInfo["received"] - returned
            _sum += gained
            completedCounter += 1
        # else:
        #   print('gained:0')

        print(
            f"{idx} | {logged_jobs[i].args['jobKey']} {logged_jobs[i].args['index']} {inv_job_state_code[int(jobInfo['status'])]} {jobInfo['received']} {returned} {gained}"
        )

        if ipfsFlag == 1 and inv_job_state_code[int(jobInfo["status"])] == "COMPLETED":
            subprocess.run(
                ["ipfs", "get", logged_jobs[i].args["jobKey"], "--output=ipfsHashes/" + logged_jobs[i].args["jobKey"],]
            )

    print(f"TOTAL_GAINED={_sum}")
    print(str(completedCounter) + "/" + str(idx - 1))


if __name__ == "__main__":
    if len(sys.argv) == 3:
        provider_address = str(sys.argv[1])
        fromBlock = int(sys.argv[2])
    else:
        provider_address = env.PROVIDER_ID
        fromBlock = 2215127

    print(fromBlock)
    getLogJobs(provider_address, fromBlock)
