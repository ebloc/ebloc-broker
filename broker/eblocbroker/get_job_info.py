#!/usr/bin/env python3

import sys
import traceback
from typing import Union

from broker import cfg
from broker._utils._log import br, log
from broker._utils.tools import print_tb
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
        print_tb(f"E: Failed to update_job_cores. {e}")
        raise e


def get_job_source_code_hashes(self, job_info, provider, job_key, index, received_block_number=0):
    """Source_code_hashes of the completed job is obtained from its event."""
    # job_id = 0
    if received_block_number == 0:
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


def get_job_info_print(job_info, provider, job_key, index, received_block_number):
    Ebb = cfg.Ebb
    elapsed_time = 0
    result_ipfs_hash = ""
    if job_info["result_ipfs_hash"] != empty_bytes32 and job_info["result_ipfs_hash"] != "":
        result_ipfs_hash = bytes32_to_ipfs(job_info["result_ipfs_hash"])

    if job_info["completion_time"]:
        elapsed_time = int(job_info["completion_time"]) - int(job_info["start_time"])

    if isinstance(job_info, dict):
        log("{0: <24}".format("==> state_code=") + f"{state.inv_code[job_info['stateCode']]} ({job_info['stateCode']})")
        log("{0: <24}".format("==> core=") + str(job_info["core"]))
        log("{0: <24}".format("==> start_time=") + str(job_info["start_time"]))
        log("{0: <24}".format("==> completion_time=") + str(job_info["completion_time"]))
        log("{0: <24}".format("==> elapsed_time=") + str(elapsed_time) + " seconds")
        log("{0: <24}".format("==> received_wei=") + str(job_info["receivedWei"]))
        log("{0: <24}".format("==> refunded_wei=") + str(job_info["refundedWei"]))
        log("{0: <24}".format("==> expected_run_time=") + str(job_info["run_time"]))
        log("{0: <24}".format("==> job_owner=") + str(job_info["job_owner"]))
        log("{0: <24}".format("==> available_core=") + str(job_info["availableCore"]))
        log("{0: <24}".format("==> price_core_min=") + str(job_info["price_core_min"]))
        log("{0: <24}".format("==> price_data_transfer=") + str(job_info["price_data_transfer"]))
        log("{0: <24}".format("==> price_storage=") + str(job_info["price_storage"]))
        log("{0: <24}".format("==> price_cache=") + str(job_info["price_cache"]))
        if result_ipfs_hash:
            log("{0: <24}".format("==> result_ipfs_hash=") + result_ipfs_hash)

        log("{0: <24}".format("==> data_transfer_in=") + str(job_info["data_transfer_in"]))
        log("{0: <24}".format("==> data_transfer_out=") + str(job_info["data_transfer_out"]))
        log(f"==> data_transfer_out_used={job_info['data_transfer_out_used']}")
        log(f"==> data_transfer_in_to_download={job_info['data_transfer_in_to_download']}")
        log(f"==> price_commitment_block_duration={job_info['commitmentBlockDuration']}")
        job_info = Ebb.get_job_source_code_hashes(job_info, provider, job_key, index, received_block_number)
        log("source_code_hashes:", "bold blue")
        for idx, code_hash in enumerate(job_info["source_code_hash"]):
            main_cloud_storage_id = job_info["cloudStorageID"][idx]
            if main_cloud_storage_id in (StorageID.IPFS, StorageID.IPFS_GPG):
                _hash = bytes32_to_ipfs(code_hash)
                _type = "ipfs_hash"
            else:
                _hash = cfg.w3.toText(code_hash)
                _type = "md5sum"

            log(br(f"{idx}, {_type}"), "bold cyan", end="")
            if len(code_hash) <= 32:
                log(f" {_hash} bytes={code_hash}", "bold")
            else:
                log(f" {_hash}\n\t{code_hash}", "bold")
    else:
        print(job_info)

    assert elapsed_time >= 0, "elapsed_time is negative"


def get_job_info(self, provider, job_key, index, job_id, received_block_number=0, is_print=True, is_log_print=False):
    """Return information of the job."""
    if is_print:
        fname = "~/ebloc-broker/broker/eblocbroker/get_job_info.py"
        log(f"{fname} {provider} \ \n\t\t{job_key} {index} {job_id} {received_block_number}", "bold cyan")

    try:
        provider = cfg.w3.toChecksumAddress(provider)
        job, received, job_owner, data_transfer_in, data_transfer_out = self._get_job_info(
            provider, job_key, int(index), int(job_id)
        )
        job_prices = self._get_provider_prices_for_job(provider, job_key, int(index))
        self.job_info = {
            "stateCode": job[0],
            "start_time": job[1],
            "received": received,
            "job_owner": job_owner.lower(),
            "data_transfer_in": data_transfer_in,
            "data_transfer_out": data_transfer_out,
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
        if received_block_number == 0:
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
    except Exception as e:
        log(f"E: Failed to get_job_info: {traceback.format_exc()}")
        raise e

    if str(self.job_info["core"]) == "0":
        log("E: Failed to get_job_info: Out of index")
        raise

    if is_log_print:
        get_job_info_print(self.job_info, provider, job_key, index, received_block_number)

    return self.job_info


def main():
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
        print("E: Please provide [provider, job_key, index, and job_id] as arguments")
        sys.exit(1)

    try:
        Ebb = cfg.Ebb
        Ebb.get_job_info(provider, job_key, index, job_id, received_block_number, is_log_print=True)
    except Exception as e:
        raise e


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print_tb(e)
