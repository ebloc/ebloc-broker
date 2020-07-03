#!/usr/bin/env python3


import sys
import traceback

import config
from config import logging
from lib import inv_job_state_code
from utils import StorageID, _colorize_traceback, bytes32_to_ipfs, empty_bytes32, log


def update_job_cores(self, job_info, provider, job_key, index, job_id=0, received_block_number=None):
    if not received_block_number:
        received_block_number = self.get_deployed_block_number()
        to_block = "latest"
    else:
        to_block = int(received_block_number)
    try:
        event_filter = config.Ebb.events.LogJob.createFilter(
            fromBlock=int(received_block_number), toBlock=to_block, argument_filters={"provider": str(provider)},
        )

        logged_jobs = event_filter.get_all_entries()
        for logged_job in logged_jobs:
            if logged_job.args["jobKey"] == job_key and logged_job.args["index"] == int(index):
                job_info.update({"core": logged_job.args["core"]})
                job_info.update({"executionDuration": logged_job.args["executionDuration"]})
                job_info.update({"cloudStorageID": logged_job.args["cloudStorageID"]})
                return job_info
            else:
                logging.error("E: Failed to find job to update")
    except Exception as e:
        _colorize_traceback()
        logging.error(f"Failed to update_job_cores: {e}")
        raise


def get_job_source_code_hashes(self, job_info, provider, job_key, index, job_id=0, received_block_number=None):
    """Source_code_hashes of the completed job is obtained from its event."""
    if received_block_number is None:
        received_block_number = self.get_deployed_block_number()
        to_block = "latest"
    else:
        to_block = int(received_block_number)

    try:
        event_filter = config.Ebb.events.LogJob.createFilter(
            fromBlock=int(received_block_number), toBlock=to_block, argument_filters={"provider": str(provider)},
        )
        logged_jobs = event_filter.get_all_entries()
        for logged_job in logged_jobs:
            if logged_job.args["jobKey"] == job_key and logged_job.args["index"] == int(index):
                job_info.update({"sourceCodeHash": logged_job.args["sourceCodeHash"]})
                return job_info
    except Exception as e:
        logging.error(f"E: Failed to get_Job_source_code_hash: {e}")
        raise


def get_job_info(self, provider, job_key, index, job_id, received_block_number=None):
    # logging.info(f"~/eBlocBroker/eblocbroke/get_job_info.py {provider} {job_key} {index} {job_id} {received_block_number}")
    try:
        provider = config.w3.toChecksumAddress(provider)
        (job, received, jobOwner, dataTransferIn, dataTransferOut,) = config.Ebb.functions.getJobInfo(
            provider, job_key, int(index), int(job_id)
        ).call()
        jobPrices = config.Ebb.functions.getProviderPricesForJob(provider, job_key, int(index)).call()

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
            "price_core_min": jobPrices[2],
            "price_data_transfer": jobPrices[3],
            "price_storage": jobPrices[4],
            "price_cache": jobPrices[5],
            "cacheType": None,
            "resultIpfsHash": "",
            "endTime": None,
            "refundedWei": None,
            "receivedBlock": None,
            "receivedWei": None,
            "cacheDuration": None,
            "sourceCodeHash": None,
            "dataTransferIn_to_download": None,
            "dataTransferOut_used": None,
        }

        job_info = self.update_job_cores(job_info, provider, job_key, index, job_id, received_block_number)
        if received_block_number is None:
            received_block_number = self.get_deployed_block_number()
        # else:
        #    to_block = int(received_block_number)

        event_filter = self.eBlocBroker.events.LogProcessPayment.createFilter(
            fromBlock=int(received_block_number), toBlock="latest", argument_filters={"provider": str(provider)},
        )

        logged_receipts = event_filter.get_all_entries()
        for logged_receipt in logged_receipts:
            if logged_receipt.args["jobKey"] == job_key and logged_receipt.args["index"] == int(index):
                job_info.update({"resultIpfsHash": logged_receipt.args["resultIpfsHash"]})
                job_info.update({"endTime": logged_receipt.args["endTime"]})
                job_info.update({"receivedWei": logged_receipt.args["receivedWei"]})
                job_info.update({"refundedWei": logged_receipt.args["refundedWei"]})
                job_info.update({"dataTransferIn_to_download": logged_receipt.args["dataTransferIn"]})
                job_info.update({"dataTransferOut_used": logged_receipt.args["dataTransferOut"]})
                break
    except Exception:
        logging.error(f"E: Failed to getJobInfo: {traceback.format_exc()}")
        raise

    if str(job_info["core"]) == "0":
        logging.error("E: Failed to getJobInfo: Out of index")
        raise

    return job_info


if __name__ == "__main__":
    import eblocbroker.Contract as Contract

    Ebb = Contract.eblocbroker
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

    try:
        job_info = get_job_info(provider, job_key, index, job_id, received_block_number)
    except:
        sys.exit(1)

    if job_info["resultIpfsHash"] == empty_bytes32:
        _resultIpfsHash = ""
    else:
        if job_info["resultIpfsHash"] != "":
            _resultIpfsHash = bytes32_to_ipfs(job_info["resultIpfsHash"])
        else:
            _resultIpfsHash = ""

    real_execution_time = 0
    if job_info["endTime"]:
        real_execution_time = int(job_info["endTime"]) - int(job_info["startTime"])

    if isinstance(job_info, dict):
        print(
            "{0: <22}".format("stateCode:")
            + f"{inv_job_state_code[job_info['jobStateCode']]} ({job_info['jobStateCode']})"
        )
        print("{0: <22}".format("core") + str(job_info["core"]))
        print("{0: <22}".format("startTime") + str(job_info["startTime"]))
        print("{0: <22}".format("endTime:") + str(job_info["endTime"]))
        print("{0: <22}".format("real_execution_time:") + str(real_execution_time) + " Seconds")
        print("{0: <22}".format("receivedWei:") + str(job_info["receivedWei"]))
        print("{0: <22}".format("refundedWei:") + str(job_info["refundedWei"]))
        print("{0: <22}".format("Expected executionDuration:") + str(job_info["executionDuration"]))
        print("{0: <22}".format("job_infoOwner:") + str(job_info["jobOwner"]))
        print("{0: <22}".format("availableCore:") + str(job_info["availableCore"]))
        print("{0: <22}".format("priceCommitmentBlockDuration:") + str(job_info["commitmentBlockDuration"]))
        print("{0: <22}".format("price_core_min:") + str(job_info["priceCoreMin"]))
        print("{0: <22}".format("price_data_transfer:") + str(job_info["priceDataTransfer"]))
        print("{0: <22}".format("price_storage:") + str(job_info["priceStorage"]))
        print("{0: <22}".format("price_cache:") + str(job_info["priceCache"]))
        print("{0: <22}".format("resultIpfsHash:") + _resultIpfsHash)
        print("{0: <22}".format("dataTransferIn:") + str(job_info["dataTransferIn"]))
        print("{0: <22}".format("dataTransferOut:") + str(job_info["dataTransferOut"]))
        print("{0: <22}".format("dataTransferIn_to_download:") + str(job_info["dataTransferIn_to_download"]))
        print("{0: <22}".format("dataTransferOut_used:") + str(job_info["dataTransferOut_used"]))

        job_info = Ebb.get_job_source_code_hashes(job_info, provider, job_key, index, job_id, received_block_number)
        # print("{0: <22}".format("source_code_hash:") + str(job_info["sourceCodeHash"]))
        log("source_code_hashes:", "blue")
        for idx, code_hash in enumerate(job_info["sourceCodeHash"]):
            main_cloud_storage_id = job_info["cloudStorageID"][idx]
            if main_cloud_storage_id in (StorageID.IPFS, StorageID.IPFS_GPG):
                _hash = bytes32_to_ipfs(code_hash)
                _type = "ipfs_hash"
            else:
                _hash = config.w3.toText(code_hash)
                _type = "md5sum"
            print(f"[{idx}] {_type}: {_hash} <= {code_hash}")
    else:
        print(job_info)
