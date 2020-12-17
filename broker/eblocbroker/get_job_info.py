#!/usr/bin/env python3

import sys
import traceback

from broker import cfg
from broker._utils._log import br, log
from broker._utils.tools import print_tb
from broker.config import logging
from broker.eblocbroker.job import DataStorage
from broker.lib import state
from broker.utils import CacheType, StorageID, bytes32_to_ipfs, empty_bytes32


def analyze_data(self, key, provider=None):
    """Obtain information related to source-code data."""
    # if not provider:
    #     provider = env.PROVIDER_ID
    current_block_number = cfg.Ebb.get_block_number()
    self.received_block = []
    self.storage_duration = []
    self.job_info["is_already_cached"] = {}
    for idx, code_hash in enumerate(self.job_info["code_hashes"]):
        if self.job_info["cloudStorageID"][idx] in (StorageID.IPFS, StorageID.IPFS_GPG):
            source_code_hash_str = source_code_hash = bytes32_to_ipfs(code_hash)
            if idx == 0 and key != source_code_hash:
                log(f"E: IPFS hash does not match with the given source_code_hash.\n\t{key} != {source_code_hash}")
                continue
        else:
            source_code_hash = code_hash
            source_code_hash_str = cfg.w3.toText(code_hash)

        received_storage_deposit = cfg.Ebb.get_received_storage_deposit(
            provider, self.job_info["job_owner"], source_code_hash
        )
        job_storage_time = cfg.Ebb.get_job_storage_time(provider, source_code_hash, _from=provider)
        ds = DataStorage(job_storage_time)
        ds.received_storage_deposit = received_storage_deposit
        self.received_block.append(ds.received_block)
        self.storage_duration.append(ds.storage_duration)
        self.job_info["is_already_cached"][source_code_hash_str] = False  # FIXME double check
        # if remaining time to cache is 0, then caching is requested for the
        # related source_code_hash
        if ds.received_block + ds.storage_duration >= current_block_number:
            if ds.received_block < current_block_number:
                self.job_info["is_already_cached"][source_code_hash_str] = True
            elif ds.received_block == current_block_number:
                if source_code_hash in self.job_info["is_already_cached"]:
                    self.job_info["is_already_cached"][source_code_hash_str] = True
                else:
                    # for the first job should be False since it is
                    # requested for cache for the first time
                    self.job_info["is_already_cached"][source_code_hash_str] = False

        log(f" * source_code_hash{br(idx)}={source_code_hash_str}")
        log(f"==> received_block={ds.received_block}")
        log(f"==> storage_duration{br(self.job_info['received_block_number'])}={ds.storage_duration}")
        log(f"==> cloud_storage_id{br(idx)}={StorageID(self.job_info['cloudStorageID'][idx]).name}")
        log(f"==> cached_type={CacheType(self.job_info['cacheType'][idx]).name}")
        log(f"==> is_already_cached={self.job_info['is_already_cached'][source_code_hash_str]}")


def set_job_received_block_number(self, received_block_number):
    if not received_block_number:
        received_block_number = self.deployed_block_number
        self.to_block = "latest"
    else:
        self.to_block = int(received_block_number)

    if int(received_block_number) > int(self.job_info["received_block_number"]):
        self.job_info["received_block_number"] = received_block_number


def update_job_cores(self, provider, job_key, index=0, received_block_number=0):
    """Update job cores."""
    self.set_job_received_block_number(received_block_number)
    try:
        event_filter = self._eBlocBroker.events.LogJob.createFilter(
            argument_filters={"provider": str(provider)},
            fromBlock=int(self.job_info["received_block_number"]),
            toBlock=self.to_block,
        )
        for logged_job in event_filter.get_all_entries():
            if logged_job.args["jobKey"] == job_key and logged_job.args["index"] == int(index):
                self.job_info["received_block_number"] = received_block_number = int(logged_job["blockNumber"])
                self.job_info.update({"core": logged_job.args["core"]})
                self.job_info.update({"run_time": logged_job.args["runTime"]})
                self.job_info.update({"cloudStorageID": logged_job.args["cloudStorageID"]})
                self.job_info.update({"cacheType": logged_job.args["cacheType"]})
                break
        else:
            logging.error("E: Failed to find job to update")

        return received_block_number
    except Exception as e:
        print_tb(f"E: Failed to update_job_cores. {e}")
        raise e


def get_job_source_code_hashes(self, provider, job_key, index, received_block_number=0):
    # job_info["received_block_number"]
    """Source_code_hashes of the completed job is obtained from its event."""
    self.set_job_received_block_number(received_block_number)
    try:
        event_filter = self._eBlocBroker.events.LogJob.createFilter(
            argument_filters={"provider": str(provider)},
            fromBlock=int(self.job_info["received_block_number"]),
            toBlock=self.to_block,
        )
        for logged_job in event_filter.get_all_entries():
            if logged_job.args["jobKey"] == job_key and logged_job.args["index"] == int(index):
                self.job_info.update({"code_hashes": logged_job.args["sourceCodeHash"]})
                break

        return self.job_info
    except Exception as e:
        logging.error(f"E: Failed to run get_job_source_code_hash(): {e}")
        raise e


def get_job_info_print(self, provider, job_key, index, received_block_number):
    Ebb = cfg.Ebb
    elapsed_time = 0
    result_ipfs_hash = ""
    if self.job_info["result_ipfs_hash"] != empty_bytes32 and self.job_info["result_ipfs_hash"] != "":
        result_ipfs_hash = bytes32_to_ipfs(self.job_info["result_ipfs_hash"])

    if self.job_info["completion_time"]:
        elapsed_time = int(self.job_info["completion_time"]) - int(self.job_info["start_time"])

    if isinstance(self.job_info, dict):
        log(f"==> state_code={state.inv_code[self.job_info['stateCode']]}({self.job_info['stateCode']})")
        log(self.job_info)
        if result_ipfs_hash:
            log(f"==> result_ipfs_hash={result_ipfs_hash}")

        Ebb.get_job_source_code_hashes(provider, job_key, index, received_block_number)
        if self.job_info["code_hashes"]:
            log("source_code_hashes:", "bold blue")
            for idx, code_hash in enumerate(self.job_info["code_hashes"]):
                main_cloud_storage_id = self.job_info["cloudStorageID"][idx]
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

        log()
        self.analyze_data(job_key, provider)
    else:
        print(self.job_info)

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
            "availableCore": job_prices[0],
            "cacheType": None,
            "stateCode": job[0],
            "start_time": job[1],
            "received": received,
            "job_owner": job_owner.lower(),
            "data_transfer_in": data_transfer_in,
            "data_transfer_out": data_transfer_out,
            "commitmentBlockDuration": job_prices[1],
            "price_core_min": job_prices[2],
            "price_data_transfer": job_prices[3],
            "price_storage": job_prices[4],
            "price_cache": job_prices[5],
            "received_block_number": received_block_number,
            "core": None,
            "run_time": None,
            "cloudStorageID": None,
            "result_ipfs_hash": "",
            "completion_time": None,
            "refundedWei": None,
            "receivedWei": None,
            "code_hashes": None,
            "data_transfer_in_to_download": None,
            "data_transfer_out_used": None,
            "storage_duration": None,
        }
        received_block_number = self.update_job_cores(provider, job_key, index, received_block_number)
        if not received_block_number or received_block_number == self.deployed_block_number:
            # First reading from the mongoDB, this will increase the speed to fetch from the logged data
            received_block_number_temp = self.mongo_broker.get_job_block_number(
                self.job_info["job_owner"], job_key, index
            )
            if received_block_number == 0 and received_block_number_temp == 0:
                received_block_number = self.deployed_block_number

            if received_block_number > self.deployed_block_number:
                self.job_info["received_block_number"] = received_block_number
        # else:
        #    to_block = int(received_block_number)
        event_filter = self._eBlocBroker.events.LogProcessPayment.createFilter(
            argument_filters={"provider": str(provider)},
            fromBlock=int(received_block_number),
            toBlock="latest",
        )
        for logged_receipt in event_filter.get_all_entries():
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
        self.get_job_info_print(provider, job_key, index, received_block_number)

    return self.job_info


def main():
    received_block_number = 0
    job_id = 0
    if len(sys.argv) > 3:
        provider = str(sys.argv[1])
        job_key = str(sys.argv[2])
        index = int(sys.argv[3])
        if len(sys.argv) == 5:
            job_id = int(sys.argv[4])

        if len(sys.argv) == 6:
            received_block_number = int(sys.argv[5])
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
