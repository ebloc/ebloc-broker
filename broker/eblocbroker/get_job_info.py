#!/usr/bin/env python3

import sys
import traceback
from typing import Union

import broker.config as config
from broker._utils.tools import _colorize_traceback, log
from broker.config import logging
from broker.lib import state
from broker.utils import StorageID, bytes32_to_ipfs, empty_bytes32


def update_job_cores(self, job_info, provider, job_key, index, received_block_number=None):
    """Update job cores."""
    # job_id = 0
    if not received_block_number:
        received_block_number = self.get_deployed_block_number()
        to_block = "latest"
    else:
        to_block = int(received_block_number)
    try:
        event_filter = self._eBlocBroker.events.LogJob.createFilter(
            fromBlock=int(received_block_number),
            toBlock=to_block,
            argument_filters={"provider": str(provider)},
        )

        logged_jobs = event_filter.get_all_entries()
        for logged_job in logged_jobs:
            if logged_job.args["jobKey"] == job_key and logged_job.args["index"] == int(index):
                job_info.update({"core": logged_job.args["core"]})
                job_info.update({"run_time": logged_job.args["runTime"]})
                job_info.update({"cloudStorageID": logged_job.args["cloudStorageID"]})
                break
        else:
            logging.error("E: Failed to find job to update")

        return job_info
    except Exception as e:
        _colorize_traceback(f"E: Failed to update_job_cores. {e}")
        raise e


def get_job_source_code_hashes(self, job_info, provider, job_key, index, received_block_number=None):
    """Source_code_hashes of the completed job is obtained from its event."""
    # job_id = 0
    if received_block_number is None:
        received_block_number = self.get_deployed_block_number()
        to_block = "latest"
    else:
        to_block = int(received_block_number)

    try:
        event_filter = self._eBlocBroker.events.LogJob.createFilter(
            fromBlock=int(received_block_number),
            toBlock=to_block,
            argument_filters={"provider": str(provider)},
        )
        logged_jobs = event_filter.get_all_entries()
        for logged_job in logged_jobs:
            if logged_job.args["jobKey"] == job_key and logged_job.args["index"] == int(index):
                job_info.update({"source_code_hash": logged_job.args["sourceCodeHash"]})
                break

        return job_info
    except Exception as e:
        logging.error(f"E: Failed to run get_job_source_code_hash(): {e}")
        raise e


def get_job_info(self, provider, job_key, index, job_id, received_block_number=None, is_print=True):
    """Return the job information."""
    if is_print:
        fname = "~/ebloc-broker/broker/eblocbroker/get_job_info.py"
        log(f"{fname} {provider} {job_key} {index} {job_id} {received_block_number}", "cyan")

    try:
        provider = config.w3.toChecksumAddress(provider)
        job, received, job_owner, data_transfer_in, data_transfer_out = self._get_job_info(
            provider, job_key, int(index), int(job_id)
        )
        job_prices = self._get_provider_prices_for_job(provider, job_key, int(index))
        self.job_info = {
            "stateCode": job[0],
            "start_time": job[1],
            "received": received,
            "job_owner": job_owner.lower(),
            "dataTransferIn": data_transfer_in,
            "dataTransferOut": data_transfer_out,
            "availableCore": job_prices[0],
            "commitmentBlockDuration": job_prices[1],
            "price_core_min": job_prices[2],
            "price_data_transfer": job_prices[3],
            "price_storage": job_prices[4],
            "price_cache": job_prices[5],
            "received_block_number": received_block_number,
            "core": None,
            "run_time": None,
            "cloudStorageID": None,
            "cacheType": None,
            "result_ipfs_hash": "",
            "completion_time": None,
            "refundedWei": None,
            "received_block": None,
            "receivedWei": None,
            "cacheDuration": None,
            "source_code_hash": None,
            "data_transfer_in_to_download": None,
            "data_transfer_out_used": None,
        }
        self.job_info = self.update_job_cores(self.job_info, provider, job_key, index, received_block_number)
        if received_block_number is None:
            # First reading from the mongoDB, this will increase the speed to fetch from the logged data
            received_block_number = self.mongo_broker.get_job_block_number(self.job_info["job_owner"], job_key, index)
            if received_block_number == 0:
                received_block_number = self.get_deployed_block_number()
            self.job_info["received_block_number"] = received_block_number
        # else:
        #    to_block = int(received_block_number)

        event_filter = self._eBlocBroker.events.LogProcessPayment.createFilter(
            fromBlock=int(received_block_number),
            toBlock="latest",
            argument_filters={"provider": str(provider)},
        )

        logged_receipts = event_filter.get_all_entries()
        for logged_receipt in logged_receipts:
            if logged_receipt.args["jobKey"] == job_key and logged_receipt.args["index"] == int(index):
                self.job_info.update({"result_ipfs_hash": logged_receipt.args["resultIpfsHash"]})
                self.job_info.update({"completion_time": logged_receipt.args["completionTime"]})
                self.job_info.update({"receivedWei": logged_receipt.args["receivedWei"]})
                self.job_info.update({"refundedWei": logged_receipt.args["refundedWei"]})
                self.job_info.update({"data_transfer_in_to_download": logged_receipt.args["dataTransferIn"]})
                self.job_info.update({"data_transfer_out_used": logged_receipt.args["dataTransferOut"]})
                break
    except Exception:
        logging.error(f"E: Failed to getJobInfo: {traceback.format_exc()}")
        raise

    if str(self.job_info["core"]) == "0":
        logging.error("E: Failed to getJobInfo: Out of index")
        raise

    return self.job_info


if __name__ == "__main__":
    import broker.eblocbroker.Contract as Contract

    Ebb = Contract.Contract()
    if len(sys.argv) == 5 or len(sys.argv) == 6:
        provider = str(sys.argv[1])
        job_key = str(sys.argv[2])
        index = int(sys.argv[3])
        job_id = int(sys.argv[4])
        if len(sys.argv) == 6:
            received_block_number = int(sys.argv[5])  # type: Union[int, None]
        else:
            received_block_number = None
    else:
        print("Please provide [provider, job_key, index, and job_id] as arguments")
        sys.exit(1)

    try:
        job_info = Ebb.get_job_info(provider, job_key, index, job_id, received_block_number)
    except Exception as e:
        _colorize_traceback(e)
        sys.exit(1)

    if job_info["result_ipfs_hash"] == empty_bytes32:
        _result_ipfs_hash = ""
    else:
        if job_info["result_ipfs_hash"] != "":
            _result_ipfs_hash = bytes32_to_ipfs(job_info["result_ipfs_hash"])
        else:
            _result_ipfs_hash = ""

    elapsed_time = 0
    if job_info["completion_time"]:
        elapsed_time = int(job_info["completion_time"]) - int(job_info["start_time"])

    if isinstance(job_info, dict):
        print("{0: <24}".format("state_code:") + f"{state.inv_code[job_info['stateCode']]} ({job_info['stateCode']})")
        print("{0: <24}".format("core") + str(job_info["core"]))
        print("{0: <24}".format("start_time") + str(job_info["start_time"]))
        print("{0: <24}".format("completion_time:") + str(job_info["completion_time"]))
        print("{0: <24}".format("elapsed_time:") + str(elapsed_time) + " seconds")
        print("{0: <24}".format("received_wei:") + str(job_info["receivedWei"]))
        print("{0: <24}".format("refunded_wei:") + str(job_info["refundedWei"]))
        print("{0: <24}".format("expected_run_time:") + str(job_info["run_time"]))
        print("{0: <24}".format("job_owner:") + str(job_info["job_owner"]))
        print("{0: <24}".format("available_core:") + str(job_info["availableCore"]))
        print("{0: <24}".format("price_core_min:") + str(job_info["price_core_min"]))
        print("{0: <24}".format("price_data_transfer:") + str(job_info["price_data_transfer"]))
        print("{0: <24}".format("price_storage:") + str(job_info["price_storage"]))
        print("{0: <24}".format("price_cache:") + str(job_info["price_cache"]))
        print("{0: <24}".format("result_ipfs_hash:") + _result_ipfs_hash)
        print("{0: <24}".format("data_transfer_in:") + str(job_info["dataTransferIn"]))
        print("{0: <24}".format("data_transfer_out:") + str(job_info["dataTransferOut"]))
        print("{0: <24}".format("data_transfer_out_used:") + str(job_info["data_transfer_out_used"]))
        print("{0: <24}".format("data_transfer_in_to_download:") + str(job_info["data_transfer_in_to_download"]))
        print("{0: <24}".format("price_commitment_block_duration:") + str(job_info["commitmentBlockDuration"]))
        job_info = Ebb.get_job_source_code_hashes(job_info, provider, job_key, index, received_block_number)
        log("source_code_hashes:", "blue")
        for idx, code_hash in enumerate(job_info["source_code_hash"]):
            main_cloud_storage_id = job_info["cloudStorageID"][idx]
            if main_cloud_storage_id in (StorageID.IPFS, StorageID.IPFS_GPG):
                _hash = bytes32_to_ipfs(code_hash)
                _type = "ipfs_hash"
            else:
                _hash = config.w3.toText(code_hash)
                _type = "md5sum"

            log(f"[{idx},{_type}] ", "cyan", end="")
            log(f"{_hash}\n\t{code_hash}")
    else:
        print(job_info)

    assert elapsed_time > 0, "elapsed_time is negative"
