#!/usr/bin/env python3

import eblocbroker.Contract as Contract
from config import env
from imports import connect
from lib import state_code

eBlocBroker, w3 = connect()
Ebb = Contract.eblocbroker

fname = f"{env.LOG_PATH}/queuedJobs.txt"

sum1 = 0
with open(fname, "r") as ins:
    for idx, line in enumerate(ins, start=1):
        output = line.split(" ")
        provider = output[1]
        job_key = output[2]
        index = output[3]

        sum1 += int(output[7]) - int(output[8])
        job_info = Ebb.get_job_info(provider, job_key, index, None)

        print(
            str(idx)
            + " "
            + output[1]
            + " "
            + output[2]
            + " "
            + output[3]
            + "|"
            + "{0: <16}".format("status:")
            + state_code[str(job_info["status"])]
            + " "
            + "{0: <16}".format('core"')
            + str(job_info["core"])
            + " "
            + "{0: <16}".format('startTime"')
            + str(job_info["startTime"])
            + " "
            + "{0: <16}".format("received:")
            + str(job_info["received"])
            + " "
            + "{0: <16}".format("coreMinPrice:")
            + str(job_info["coreMinPrice"])
            + " "
            + "{0: <16}".format("memoryMinPrice:")
            + str(job_info["memoryMinPrice"])
            + " "
            + "{0: <16}".format("coreMinuteGas:")
            + str(job_info["coreMinuteGas"])
            + " "
            + "{0: <16}".format("job_infoOwner:")
            + job_info["job_owner"]
        )

print(f"GAINED={sum1}")
