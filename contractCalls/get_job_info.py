#!/usr/bin/env python3


import sys
import traceback

import config
from lib import StorageID, inv_job_state_code
from config import logging
from imports import connect
from utils import bytes32_to_ipfs, empty_bytes32
from contractCalls.get_deployed_block_number import get_deployed_block_number


config.eBlocBroker, config.w3 = connect()


def update_job_cores(job_info, provider, job_key, index, job_id, received_block_number=None):
    if config.eBlocBroker is None or config.w3 is None:
        return False, "notconnected"

    if not received_block_number:
        received_block_number = get_deployed_block_number()
        to_block = "latest"
    else:
        to_block = int(received_block_number)
    try:
        event_filter = config.eBlocBroker.events.LogJob.createFilter(
            fromBlock=int(received_block_number), toBlock=to_block, argument_filters={"provider": str(provider)}
        )
        logged_jobs = event_filter.get_all_entries()
        for logged_job in logged_jobs:
            if logged_job.args["jobKey"] == job_key and logged_job.args["index"] == int(index):
                job_info.update({"core": logged_job.args["core"]})
                job_info.update({"executionDuration": logged_job.args["executionDuration"]})
                job_info.update({"cloudStorageID": logged_job.args["cloudStorageID"]})
                return True, job_info
    except Exception as e:
        return False, f"Failed to update_job_cores: {e}"


def get_job_source_code_hashes(job_info, provider, job_key, index, job_id, received_block_number=None):
    """source_code_hashes of the completed job is obtained from its event"""
    if config.eBlocBroker is None or config.w3 is None:
        return False, "notconnected"

    if received_block_number is None:
        received_block_number = get_deployed_block_number()
        to_block = "latest"
    else:
        to_block = int(received_block_number)

    try:
        event_filter = config.eBlocBroker.events.LogJob.createFilter(
            fromBlock=int(received_block_number), toBlock=to_block, argument_filters={"provider": str(provider)}
        )
        logged_jobs = event_filter.get_all_entries()
        for logged_job in logged_jobs:
            if logged_job.args["jobKey"] == job_key and logged_job.args["index"] == int(index):
                job_info.update({"sourceCodeHash": logged_job.args["sourceCodeHash"]})
                return True, job_info
    except Exception as e:
        return False, f"E: Failed to get_Job_source_code_hash: {e}"


def get_job_info(provider, job_key, index, job_id, received_block_number=None):
    logging.info(f"~/eBlocBroker/contractCalls/get_job_info.py {provider} {job_key} {index} {job_id} {received_block_number}")
    if config.eBlocBroker is None or config.w3 is None:
        return False, "notconnected"

    try:
        provider = config.w3.toChecksumAddress(provider)
        (job, received, jobOwner, dataTransferIn, dataTransferOut) = config.eBlocBroker.functions.getJobInfo(
            provider, job_key, int(index), int(job_id)
        ).call()
        jobPrices = config.eBlocBroker.functions.getProviderPricesForJob(provider, job_key, int(index)).call()

        job_info = {
            "startTime": job[0],
            "jobStateCode": job[1],
            "core": None,
            "executionDuration": None,
            "cloudStorageID": None,
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
        success, jobCores = update_job_cores(job_info, provider, job_key, index, job_id, received_block_number)
        if received_block_number is None:
            received_block_number = get_deployed_block_number()
        # else:
        #    to_block = int(received_block_number)

        event_filter = config.eBlocBroker.events.LogProcessPayment.createFilter(
            fromBlock=int(received_block_number), toBlock="latest", argument_filters={"provider": str(provider)}
        )

        logged_receipts = event_filter.get_all_entries()
        for logged_receipt in logged_receipts:
            if logged_receipt.args["jobKey"] == job_key and logged_receipt.args["index"] == int(index):
                job_info.update({"resultIpfsHash": logged_receipt.args["resultIpfsHash"]})
                job_info.update({"endTime": logged_receipt.args["endTime"]})
                job_info.update({"receivedWei": logged_receipt.args["receivedWei"]})
                job_info.update({"refundedWei": logged_receipt.args["refundedWei"]})
                job_info.update({"dataTransferIn_used": logged_receipt.args["dataTransferIn"]})
                job_info.update({"dataTransferOut_used": logged_receipt.args["dataTransferOut"]})
                break

    except Exception:
        return False, f"E: Failed to getJobInfo: {traceback.format_exc()}"

    if str(job_info["core"]) == "0":
        return False, "E: Failed to getJobInfo: Out of index"

    return True, job_info


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

    success, job_info = get_job_info(provider, job_key, index, job_id, received_block_number)

    if not success:
        print(job_info)
        sys.exit(1)

    if job_info["resultIpfsHash"] == empty_bytes32:
        _resultIpfsHash = ""
    else:
        if job_info["resultIpfsHash"] != "":
            _resultIpfsHash = bytes32_to_ipfs(job_info["resultIpfsHash"])
        else:
            _resultIpfsHash = ""

    realExecutionTime = 0
    if job_info["endTime"] is not None:
        realExecutionTime = int(job_info["endTime"]) - int(job_info["startTime"])

    if type(job_info) is dict:
        print("{0: <22}".format("stateCode:") + f"{inv_job_state_code[job_info['jobStateCode']]} ({job_info['jobStateCode']})")
        print("{0: <22}".format("core") + str(job_info["core"]))
        print("{0: <22}".format("startTime") + str(job_info["startTime"]))
        print("{0: <22}".format("endTime:") + str(job_info["endTime"]))
        print("{0: <22}".format("realExecutionTime:") + str(realExecutionTime) + " Seconds")
        print("{0: <22}".format("receivedWei:") + str(job_info["receivedWei"]))
        print("{0: <22}".format("refundedWei:") + str(job_info["refundedWei"]))
        print("{0: <22}".format("Expected executionDuration:") + str(job_info["executionDuration"]))
        print("{0: <22}".format("job_infoOwner:") + str(job_info["jobOwner"]))
        print("{0: <22}".format("availableCore:") + str(job_info["availableCore"]))
        print("{0: <22}".format("priceCommitmentBlockDuration:") + str(job_info["commitmentBlockDuration"]))
        print("{0: <22}".format("priceCoreMin:") + str(job_info["priceCoreMin"]))
        print("{0: <22}".format("priceDataTransfer:") + str(job_info["priceDataTransfer"]))
        print("{0: <22}".format("priceStorage:") + str(job_info["priceStorage"]))
        print("{0: <22}".format("priceCache:") + str(job_info["priceCache"]))
        print("{0: <22}".format("resultIpfsHash:") + _resultIpfsHash)
        print("{0: <22}".format("dataTransferIn:") + str(job_info["dataTransferIn"]))
        print("{0: <22}".format("dataTransferOut:") + str(job_info["dataTransferOut"]))
        print("{0: <22}".format("dataTransferIn_used:") + str(job_info["dataTransferIn_used"]))
        print("{0: <22}".format("dataTransferOut_used:") + str(job_info["dataTransferOut_used"]))

        success, job_info = get_job_source_code_hashes(job_info, provider, job_key, index, job_id, received_block_number)
        # print("{0: <22}".format("source_code_hash:") + str(job_info["sourceCodeHash"]))
        print("source_code_hashes:")
        for idx, code_hash in enumerate(job_info["sourceCodeHash"]):
            main_cloud_storage_id = job_info["cloudStorageID"][idx]
            if main_cloud_storage_id == StorageID.IPFS.value or main_cloud_storage_id == StorageID.IPFS_MINILOCK.value:
                _hash = bytes32_to_ipfs(code_hash)
                _type = "ipfs_hash"
            else:
                _hash = config.w3.toText(code_hash)
                _type = "md5sum"

            print(f"[{idx}] {_type}: {_hash} <= {code_hash}")
    else:
        print(job_info)
