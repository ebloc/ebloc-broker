#!/usr/bin/env python3


import sys
import traceback

import lib
from config import logging
from imports import connect
from utils import bytes32_to_ipfs, empty_bytes32


def update_job_cores(jobInfo, provider, job_key, index, job_id, received_block_number=None):
    eBlocBroker, w3 = connect()
    if eBlocBroker is None or w3 is None:
        return False, "notconnected"

    if received_block_number is None:
        received_block_number = 3082590  # Point where the eBlocBroker contract deployed
        _toBlock = "latest"
    else:
        _toBlock = int(received_block_number)

    try:
        event_filter = eBlocBroker.events.LogJob.createFilter(
            fromBlock=int(received_block_number), toBlock=_toBlock, argument_filters={"provider": str(provider)},
        )
        logged_jobs = event_filter.get_all_entries()
        for logged_job in logged_jobs:
            if logged_job.args["jobKey"] == job_key and logged_job.args["index"] == int(index):
                jobInfo.update({"core": logged_job.args["core"]})
                jobInfo.update({"executionDuration": logged_job.args["executionDuration"]})
                return True, jobInfo
    except Exception as e:
        return False, f"Failed to update_job_cores: {e}"


def get_job_source_code_hashes(jobInfo, provider, job_key, index, job_id, received_block_number=None):
    eBlocBroker, w3 = connect()
    if eBlocBroker is None or w3 is None:
        return False, "notconnected"

    if received_block_number is None:
        received_block_number = 3082590  # Point where the eBlocBroker contract deployed
        _toBlock = "latest"
    else:
        _toBlock = int(received_block_number)

    try:
        event_filter = eBlocBroker.events.LogJob.createFilter(
            fromBlock=int(received_block_number), toBlock=_toBlock, argument_filters={"provider": str(provider)},
        )
        logged_jobs = event_filter.get_all_entries()
        for logged_job in logged_jobs:
            if logged_job.args["jobKey"] == job_key and logged_job.args["index"] == int(index):
                jobInfo.update({"sourceCodeHash": logged_job.args["sourceCodeHash"]})
                return True, jobInfo
    except Exception as e:
        return False, f"Failed to get_Job_source_code_hash: {e}"


def get_job_info(provider, job_key, index, job_id, received_block_number=None):
    logging.info(f"./get_job_info.py {provider} {job_key} {index} {job_id} {received_block_number}")
    if received_block_number is None:
        received_block_number = 3082590  # Point where the eBlocBroker is contract deployed
        # _toBlock = "latest"
    # else:
    #    _toBlock = int(received_block_number)

    eBlocBroker, w3 = connect()
    if eBlocBroker is None or w3 is None:
        return False, "notconnected"
    try:
        provider = w3.toChecksumAddress(provider)
        (job, received, jobOwner, dataTransferIn, dataTransferOut,) = eBlocBroker.functions.getJobInfo(
            provider, job_key, int(index), int(job_id)
        ).call()
        jobPrices = eBlocBroker.functions.getProviderPricesForJob(provider, job_key, int(index)).call()

        jobInfo = {
            "startTime": job[0],
            "jobStateCode": job[1],
            "core": None,
            "executionDuration": None,
            "received": received,
            "jobOwner": jobOwner,
            "dataTransferIn": dataTransferIn,
            "dataTransferOut": dataTransferOut,
            "availableCore": jobPrices[0],
            "commitmentBlockDuration": jobPrices[1],
            "priceCoreMin": jobPrices[2],
            "priceDataTransfer": jobPrices[3],
            "priceStorage": jobPrices[4],
            "priceCache": jobPrices[5],
            "cacheType": None,
            "resultIpfsHash": "",
            "endTime": None,
            "refundedWei": None,
            "receivedBlock": None,
            "receivedWei": None,
            "cacheDuration": None,
            "sourceCodeHash": None,
            "dataTransferIn_used": None,
            "dataTransferOut_used": None,
        }
        success, jobCores = update_job_cores(jobInfo, provider, job_key, index, job_id, received_block_number)
        # resultIpfsHash = ""
        event_filter = eBlocBroker.events.LogProcessPayment.createFilter(
            fromBlock=int(received_block_number), toBlock="latest", argument_filters={"provider": str(provider)},
        )

        logged_receipts = event_filter.get_all_entries()
        for logged_receipt in logged_receipts:
            if logged_receipt.args["jobKey"] == job_key and logged_receipt.args["index"] == int(index):
                jobInfo.update({"resultIpfsHash": logged_receipt.args["resultIpfsHash"]})
                jobInfo.update({"endTime": logged_receipt.args["endTime"]})
                jobInfo.update({"receivedWei": logged_receipt.args["receivedWei"]})
                jobInfo.update({"refundedWei": logged_receipt.args["refundedWei"]})
                jobInfo.update({"dataTransferIn_used": logged_receipt.args["dataTransferIn"]})
                jobInfo.update({"dataTransferOut_used": logged_receipt.args["dataTransferOut"]})
                break

    except Exception:
        return False, f"E: Failed to getJobInfo: {traceback.format_exc()}"

    if str(jobInfo["core"]) == "0":
        return False, "E: Failed to getJobInfo: Out of index"

    return True, jobInfo


if __name__ == "__main__":
    if len(sys.argv) == 5 or len(sys.argv) == 6:
        provider = str(sys.argv[1])
        job_key = str(sys.argv[2])
        index = int(sys.argv[3])
        job_id = int(sys.argv[4])
        if len(sys.argv) == 6:
            received_block_number = int(sys.argv[5])
        else:
            received_block_number = None
    else:
        print("Please provide {provider, job_key, index, and job_id} as arguments")
        sys.exit(1)

    # received_block_number = 3157313
    success, jobInfo = get_job_info(provider, job_key, index, job_id, received_block_number)

    if not success:
        print(jobInfo)
        sys.exit(1)

    if jobInfo["resultIpfsHash"] == empty_bytes32:
        _resultIpfsHash = ""
    else:
        if jobInfo["resultIpfsHash"] != "":
            _resultIpfsHash = bytes32_to_ipfs(jobInfo["resultIpfsHash"])
        else:
            _resultIpfsHash = ""

    realExecutionTime = 0
    if jobInfo["endTime"] is not None:
        realExecutionTime = int(jobInfo["endTime"]) - int(jobInfo["startTime"])

    if type(jobInfo) is dict:
        print(
            "{0: <22}".format("stateCode:")
            + f"{lib.inv_job_state_code[jobInfo['jobStateCode']]} ({jobInfo['jobStateCode']})"
        )
        print("{0: <22}".format("core") + str(jobInfo["core"]))
        print("{0: <22}".format("startTime") + str(jobInfo["startTime"]))
        print("{0: <22}".format("endTime:") + str(jobInfo["endTime"]))
        print("{0: <22}".format("realExecutionTime:") + str(realExecutionTime) + " Seconds")
        print("{0: <22}".format("receivedWei:") + str(jobInfo["receivedWei"]))
        print("{0: <22}".format("refundedWei:") + str(jobInfo["refundedWei"]))
        print("{0: <22}".format("Expected executionDuration:") + str(jobInfo["executionDuration"]))
        print("{0: <22}".format("jobInfoOwner:") + str(jobInfo["jobOwner"]))
        print("{0: <22}".format("availableCore:") + str(jobInfo["availableCore"]))
        print("{0: <22}".format("priceCommitmentBlockDuration:") + str(jobInfo["commitmentBlockDuration"]))
        print("{0: <22}".format("priceCoreMin:") + str(jobInfo["priceCoreMin"]))
        print("{0: <22}".format("priceDataTransfer:") + str(jobInfo["priceDataTransfer"]))
        print("{0: <22}".format("priceStorage:") + str(jobInfo["priceStorage"]))
        print("{0: <22}".format("priceCache:") + str(jobInfo["priceCache"]))
        print("{0: <22}".format("resultIpfsHash:") + _resultIpfsHash)
        print("{0: <22}".format("dataTransferIn:") + str(jobInfo["dataTransferIn"]))
        print("{0: <22}".format("dataTransferOut:") + str(jobInfo["dataTransferOut"]))
        print("{0: <22}".format("dataTransferIn_used:") + str(jobInfo["dataTransferIn_used"]))
        print("{0: <22}".format("dataTransferOut_used:") + str(jobInfo["dataTransferOut_used"]))

        success, jobInfo = get_job_source_code_hashes(jobInfo, provider, job_key, index, job_id, received_block_number)
        print("{0: <22}".format("sourceCodeHash:") + str(jobInfo["sourceCodeHash"]))
    else:
        print(jobInfo)
