#!/usr/bin/env python3

"""
Guide asynchronous polling: http://web3py.readthedocs.io/en/latest/filters.html#examples-listening-for-events
"""

import sys
import time

import lib
from imports import connect
from utils import bytes32_to_ipfs


def logReturn(event_filter, poll_interval):
    while True:
        logged_jobs = event_filter.get_new_entries()
        if len(logged_jobs) > 0:
            return logged_jobs
        time.sleep(poll_interval)


def run_log_job(from_block, provider):
    eBlocBroker, w3 = connect()
    if eBlocBroker is None or w3 is None:
        return

    event_filter = eBlocBroker.events.LogJob.createFilter(
        fromBlock=int(from_block), toBlock="latest", argument_filters={"provider": str(provider)},
    )
    logged_jobs = event_filter.get_all_entries()

    if len(logged_jobs) > 0:
        return logged_jobs
    else:
        return logReturn(event_filter, 2)


def run_log_cancel_refund(from_block, provider):
    eBlocBroker, w3 = connect()
    if eBlocBroker is None or w3 is None:
        return

    event_filter = eBlocBroker.events.LogRefund.createFilter(
        fromBlock=int(from_block), argument_filters={"provider": str(provider)}
    )
    logged_cancelled_jobs = event_filter.get_all_entries()
    if len(logged_cancelled_jobs) > 0:
        return logged_cancelled_jobs
    else:
        return logReturn(event_filter, 2)


def run_single_log_job(from_block, jobKey, transactionHash):
    eBlocBroker, w3 = connect()
    if eBlocBroker is None or w3 is None:
        return

    event_filter = eBlocBroker.events.LogJob.createFilter(
        fromBlock=int(from_block), argument_filters={"provider": str(provider)}
    )
    logged_jobs = event_filter.get_all_entries()

    if len(logged_jobs) > 0:
        for logged_job in logged_jobs:
            if logged_job["transactionHash"].hex() == transactionHash:
                return logged_job["index"]
    else:
        return logReturn(event_filter, 2)


if __name__ == "__main__":
    if len(sys.argv) == 3:
        from_block = int(sys.argv[1])
        provider = str(sys.argv[2])  # Only obtains jobs that are submitted to the provider.
    else:
        from_block = 3070724
        provider = "0x57b60037b82154ec7149142c606ba024fbb0f991"

    logged_jobs = run_log_job(from_block, provider)

    for logged_job in logged_jobs:
        # print(logged_jobs[i])
        cloudStorageID = logged_job.args["cloudStorageID"]
        """
        if lib.StorageID.IPFS.value == cloudStorageID or lib.cloudStorageID.IPFS_MINILOCK.value == cloudStorageID:
            jobKey = bytes32_to_ipfs(logged_jobs[i].args['jobKey'])
        else:
            jobKey = logged_jobs[i].args['jobKey']
        """

        print(f"transactionHash={logged_job['transactionHash'].hex()} | logIndex={logged_job['logIndex']}")
        print("blockNumber: " + str(logged_job["blockNumber"]))
        print("provider: " + logged_job.args["provider"])
        print("jobKey: " + logged_job.args["jobKey"])
        print("index: " + str(logged_job.args["index"]))
        print("cloudStorageID: " + str(lib.StorageID(cloudStorageID).name))
        print("cacheType: " + str(lib.CacheType(logged_job.args["cacheType"]).name))
        print("received: " + str(logged_job.args["received"]))

        for value in logged_job.args["sourceCodeHash"]:
            sourceCodeHash = logged_job.args["sourceCodeHash"][value]
            print("sourceCodeHash[" + str(value) + "]: " + bytes32_to_ipfs(sourceCodeHash))

        print("-------------------------------------------------------------------------------")

# bytes32[] sourceCodeHash,
# uint8 cacheType,
# uint received);
