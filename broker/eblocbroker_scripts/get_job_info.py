#!/usr/bin/env python3

import sys

from broker import cfg
from broker._utils._log import br, log
from broker._utils.tools import print_tb
from broker.eblocbroker_scripts.get_transaction_receipt import get_msg_value
from broker.eblocbroker_scripts.job import DataStorage
from broker.lib import state
from broker.utils import CacheType, StorageID, bytes32_to_ipfs, empty_bytes32

Ebb = cfg.Ebb


def analyze_data(self, key, provider=None):
    """Obtain information related to source-code data."""
    current_bn = Ebb.get_block_number()
    self.received_block = []
    self.storage_duration = []
    self.job_info["is_cached"] = {}
    for idx, code_hash in enumerate(self.job_info["code_hashes"]):
        if self.job_info["cloudStorageID"][idx] in (StorageID.IPFS, StorageID.IPFS_GPG):
            _type = "ipfs_hash"
            code_hash = code_hash_str = bytes32_to_ipfs(code_hash)
            if idx == 0 and key != code_hash:
                log(f"E: IPFS hash does not match with the given code_hash.\n\t{key} != {code_hash}")
                continue
        else:
            _type = "md5sum"
            code_hash_str = cfg.w3.toText(code_hash)

        received_deposit, *_ = Ebb.get_storage_info(code_hash, provider, self.job_info["job_owner"])
        *_, job_storage_duration = Ebb.get_job_storage_duration(provider, cfg.ZERO_ADDRESS, code_hash)
        ds = DataStorage(job_storage_duration)
        ds.received_deposit = received_deposit
        self.received_block.append(ds.received_block)
        self.storage_duration.append(ds.storage_duration)
        self.job_info["is_cached"][code_hash_str] = False  # FIXME double check
        # if remaining time to cache is 0, then caching is requested for the
        # related code_hash
        if ds.received_block + ds.storage_duration >= current_bn:
            if ds.received_block < current_bn:
                self.job_info["is_cached"][code_hash_str] = True
            elif ds.received_block == current_bn:
                if code_hash in self.job_info["is_cached"]:
                    self.job_info["is_cached"][code_hash_str] = True
                else:
                    # for the first job should be False since it is
                    # requested for cache for the first time
                    self.job_info["is_cached"][code_hash_str] = False

        log(br(f"{idx}, {_type}"), "bold cyan", end="")
        if len(code_hash) <= 32:
            log(f" {code_hash_str} bytes={code_hash} ", "bold", end="")
        else:
            if _type == "ipfs_hash":
                log(f" {code_hash_str} ", "bold", end="")
            else:
                log(f" {code_hash_str} {code_hash} ", "bold", end="")

        log(CacheType(self.job_info["cacheType"][idx]).name, "bold magenta", end="")
        log(" ", end="")
        log(StorageID(self.job_info["cloudStorageID"][idx]).name, "bold", end="")
        log(" ", end="")
        log(f"is_cached={self.job_info['is_cached'][code_hash_str]}", "bold", end="")
        if ds.received_block > 0:
            log(f" received_block={ds.received_block}", "bold", end="")

        if ds.storage_duration > 0:
            log(f" storage_dur={ds.storage_duration}", "bold", end="")

        log()


def set_job_received_bn(self, received_bn):
    if not received_bn:
        received_bn = self.deployed_block_number
        self.to_block = "latest"
    else:
        self.to_block = int(received_bn)

    if int(received_bn) > int(self.job_info["received_bn"]):
        self.job_info["received_bn"] = received_bn


def update_job_cores(self, provider, job_key, index=0, received_bn=0) -> int:
    """Update job cores."""
    self.set_job_received_bn(received_bn)
    try:
        event_filter = self._eblocbroker.events.LogJob.createFilter(
            argument_filters={"provider": str(provider)},
            fromBlock=int(self.job_info["received_bn"]),
            toBlock=self.to_block,
        )
        for logged_job in event_filter.get_all_entries():
            if logged_job.args["jobKey"] == job_key and logged_job.args["index"] == int(index):
                self.job_info["received_bn"] = received_bn = int(logged_job["blockNumber"])
                self.job_info.update({"core": logged_job.args["core"]})
                self.job_info.update({"run_time": logged_job.args["runTime"]})
                self.job_info.update({"cloudStorageID": logged_job.args["cloudStorageID"]})
                self.job_info.update({"cacheType": logged_job.args["cacheType"]})
                self.job_info.update({"submitJob_tx_hash": logged_job["transactionHash"].hex()})
                self.job_info.update(
                    {
                        "submitJob_msg_value": get_msg_value(
                            logged_job["blockHash"].hex(), logged_job["transactionIndex"]
                        )
                    }
                )
                break
        else:
            log(f"E: failed to find and update job({job_key})")

        return received_bn
    except Exception as e:
        print_tb(f"E: Failed to update job cores.\n{e}")
        raise e


def get_job_code_hashes(self, provider, job_key, index, received_bn=0):
    """Return code hashes of the completed job is obtained from its event."""
    # job_info["received_bn"]
    self.set_job_received_bn(received_bn)
    try:
        event_filter = self._eblocbroker.events.LogJob.createFilter(
            argument_filters={"provider": str(provider)},
            fromBlock=int(self.job_info["received_bn"]),
            toBlock=self.to_block,
        )
        for logged_job in event_filter.get_all_entries():
            if logged_job.args["jobKey"] == job_key and logged_job.args["index"] == int(index):
                self.job_info.update({"code_hashes": logged_job.args["sourceCodeHash"]})
                break

        return self.job_info
    except Exception as e:
        log(f"E: Failed to run `get_job_code_hashes()` function\n{e}")
        raise e


def get_job_info_print(self, provider, job_key, index, received_bn):
    result_ipfs_hash = ""
    if self.job_info["result_ipfs_hash"] != empty_bytes32 and self.job_info["result_ipfs_hash"] != "":
        result_ipfs_hash = bytes32_to_ipfs(self.job_info["result_ipfs_hash"])

    if isinstance(self.job_info, dict):
        log(f" * state_code={state.inv_code[self.job_info['stateCode']]}({self.job_info['stateCode']})")
        if result_ipfs_hash:
            log(f"==> result_ipfs_hash={result_ipfs_hash}")

        Ebb.get_job_code_hashes(provider, job_key, index, received_bn)
        self.analyze_data(job_key, provider)
    else:
        print(self.job_info)


def get_job_info(self, provider, job_key, index, job_id, received_bn=0, is_print=True, is_log_print=False):
    """Return information of the job."""
    if is_print:
        fn = "~/ebloc-broker/broker/eblocbroker_scripts/get_job_info.py"
        log(f"$ {fn} {provider} {job_key} {index} {job_id} {received_bn}", "bold cyan", is_code=True)

    try:
        provider = cfg.w3.toChecksumAddress(provider)
        job, received, job_owner, data_transfer_in, data_transfer_out = self._get_job_info(
            provider, job_key, int(index), int(job_id)
        )
        job_prices = self._get_provider_prices_for_job(provider, job_key, int(index))

        self.job_info = {
            "provider": provider,
            "job_key": job_key,
            "index": index,
            "availableCore": job_prices[0],
            "cacheType": None,
            "stateCode": job[0],
            "start_timestamp": job[1],
            "received": received,
            "job_owner": job_owner.lower(),
            "data_transfer_in": data_transfer_in,
            "data_transfer_out": data_transfer_out,
            "commitment_block_duration": job_prices[1],
            "price_core_min": job_prices[2],
            "price_data_transfer": job_prices[3],
            "price_storage": job_prices[4],
            "price_cache": job_prices[5],
            "received_bn": received_bn,
            "core": None,
            "run_time": None,
            "actual_elapsed_time": None,
            "cloudStorageID": None,
            "result_ipfs_hash": "",
            "refunded_gwei": None,
            "received_gwei": None,
            "code_hashes": None,
            "data_transfer_in_to_download": None,
            "data_transfer_out_used": None,
            "storage_duration": None,
            "submitJob_tx_hash": None,
            "processPayment_tx_hash": None,
            "submitJob_msg_value": 0,
        }
        received_bn = self.update_job_cores(provider, job_key, index, received_bn)
        if not received_bn or received_bn == self.deployed_block_number:
            # First reading from the mongoDB, this will increase the speed to fetch from the logged data
            received_bn_temp = self.mongo_broker.get_job_block_number(self.job_info["job_owner"], job_key, index)
            if received_bn == 0 and received_bn_temp == 0:
                received_bn = self.deployed_block_number

            if received_bn > self.deployed_block_number:
                self.job_info["received_bn"] = received_bn
        # else:
        #    to_block = int(received_bn)
        event_filter = self._eblocbroker.events.LogProcessPayment.createFilter(
            argument_filters={"provider": str(provider)},
            fromBlock=int(received_bn),
            toBlock="latest",
        )
        for logged_receipt in event_filter.get_all_entries():
            if logged_receipt.args["jobKey"] == job_key and logged_receipt.args["index"] == int(index):
                self.job_info.update({"result_ipfs_hash": logged_receipt.args["resultIpfsHash"]})
                self.job_info.update({"received_gwei": logged_receipt.args["receivedGwei"]})
                self.job_info.update({"refunded_gwei": logged_receipt.args["refundedGwei"]})
                self.job_info.update({"data_transfer_in_to_download": logged_receipt.args["dataTransferIn"]})
                self.job_info.update({"data_transfer_out_used": logged_receipt.args["dataTransferOut"]})
                self.job_info.update({"data_transfer_out_used": logged_receipt.args["dataTransferOut"]})
                self.job_info.update({"actual_elapsed_time": logged_receipt.args["elapsedTime"]})
                self.job_info.update({"processPayment_tx_hash": logged_receipt["transactionHash"].hex()})
                if self.job_info["result_ipfs_hash"] == empty_bytes32:
                    self.job_info.update({"result_ipfs_hash": b""})

                break
    except Exception as e:
        raise e

    if str(self.job_info["core"]) == "0":
        raise Exception("Failed to get_job_info: Out of index")

    if is_log_print:
        self.get_job_info_print(provider, job_key, index, received_bn)
        log(self.job_info)

    if not self.job_info["storage_duration"]:
        self.job_info["storage_duration"] = []
        for _ in range(len(self.job_info["cacheType"])):
            self.job_info["storage_duration"].append(0)

    return self.job_info


def main():
    received_bn = 0
    job_id = 0
    if len(sys.argv) > 3:
        provider = str(sys.argv[1])
        job_key = str(sys.argv[2])
        index = int(sys.argv[3])
        if len(sys.argv) == 5:
            job_id = int(sys.argv[4])

        if len(sys.argv) == 6:
            received_bn = int(sys.argv[5])
    else:
        log("E: Provide <provider, [m]job_key[/m], [m]index[/m], and [m]job_id[/m]> as arguments")
        sys.exit(1)

    Ebb.get_job_info(provider, job_key, index, job_id, received_bn, is_log_print=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception as e:
        print_tb(e)
