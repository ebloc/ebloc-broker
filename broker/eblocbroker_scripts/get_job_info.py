#!/usr/bin/env python3

import sys

from broker import cfg
from broker._utils._log import br, log
from broker._utils.tools import print_tb
from broker.eblocbroker_scripts.job import DataStorage
from broker.errors import QuietExit
from broker.lib import state
from broker.utils import CacheType, StorageID, bytes32_to_ipfs, empty_bytes32

Ebb = cfg.Ebb


def analyze_data(self, key, provider=None):
    """Obtain the information related to data file."""
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

        log(br(f"{idx},{_type}"), "cyan", end="")
        if len(code_hash) <= 32:
            log(f" {code_hash_str} bytes={code_hash} ", end="")
        else:
            if _type == "ipfs_hash":
                log(f" {code_hash_str} ", end="")
            else:
                log(f" {code_hash_str} {code_hash} ", end="")

        log(CacheType(self.job_info["cacheType"][idx]).name, "magenta", end="")
        log(" ", end="")
        log(StorageID(self.job_info["cloudStorageID"][idx]).name, end="")
        log(" ", end="")
        if StorageID(self.job_info["cloudStorageID"][idx]).name.lower() != "none":
            log(f"is_cached={self.job_info['is_cached'][code_hash_str]}", end="")
        else:
            log("dataset", "yellow", end="")

        if ds.received_block > 0:
            log(f" received_bn={ds.received_block}", end="")

        if ds.storage_duration > 0:
            log(f" storage_dur={ds.storage_duration}", end="")

        log()


def set_job_received_bn(self, received_bn):
    if received_bn:
        self.to_block = int(received_bn)
    else:
        received_bn = self.deployed_block_number
        self.to_block = "latest"

    if int(received_bn) > int(self.job_info["received_bn"]):
        self.job_info["received_bn"] = received_bn


def fetch_log_data_storage_request(self, tx_by_block):
    event_filter = self._eblocbroker.events.LogDataStorageRequest.createFilter(
        # argument_filters={"provider": str(provider)},
        fromBlock=int(tx_by_block["blockNumber"]),
        toBlock=int(tx_by_block["blockNumber"]),
    )

    log_data_storage_request_list = []
    for logged_job in event_filter.get_all_entries():
        if tx_by_block["hash"] == logged_job["transactionHash"]:
            log_data_storage_request_list.append(dict(logged_job["args"]))

    if log_data_storage_request_list:
        self.job_info.update({"submitJob_LogDataStorageRequest": log_data_storage_request_list})


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
                self.job_info.update({"submitJob_received_job_price": logged_job.args["received"]})  #
                self.job_info.update({"submitJob_tx_hash": logged_job["transactionHash"].hex()})
                self.job_info.update({"submitJob_block_hash": logged_job["blockHash"].hex()})
                tx_by_block = Ebb.get_transaction_by_block(
                    self.job_info["submitJob_block_hash"], logged_job["transactionIndex"]
                )
                # self.job_info.update({"submitJob_received_job_price": int(tx_by_block["value"] / 10**9)})
                tx_receipt = Ebb.get_transaction_receipt(self.job_info["submitJob_tx_hash"])
                tx_by_block = Ebb.get_transaction_by_block(
                    tx_receipt["blockHash"].hex(), tx_receipt["transactionIndex"]
                )
                output = Ebb.eBlocBroker.decode_input(tx_by_block["input"])
                if output:
                    output = output[1]
                    self.job_info.update({"data_transfer_in_input": output[1]})
                    self.job_info.update({"data_transfer_out_input": output[2][-2]})
                    self.job_info.update({"received": output[2][-1]})
                    self.job_info.update({"storage_duration": output[3]})
                    self.job_info.update({"data_prices_set_block_numbers": output[2][4]})

                self.job_info.update({"submitJob_gas_used": int(tx_receipt["gasUsed"])})
                break
        else:
            log(f"E: failed to find and update job({job_key})")

        self.fetch_log_data_storage_request(tx_by_block)
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


def get_job_info_print(self, provider, job_key, index, received_bn, is_print=True):
    result_ipfs_hash = ""
    if self.job_info["result_ipfs_hash"] != empty_bytes32 and self.job_info["result_ipfs_hash"] != "":
        result_ipfs_hash = bytes32_to_ipfs(self.job_info["result_ipfs_hash"])

    if isinstance(self.job_info, dict):
        if is_print:
            log(f" * state_code={state.inv_code[self.job_info['stateCode']]}({self.job_info['stateCode']})")

            if result_ipfs_hash:
                log(f"==> result_ipfs_hash={result_ipfs_hash}")

        Ebb.get_job_code_hashes(provider, job_key, index, received_bn)
        if is_print:
            self.analyze_data(job_key, provider)
    elif is_print:
        print(self.job_info)


def get_job_info(
    self, provider, job_key, index, job_id, received_bn=0, is_print=True, is_log_print=False, is_fetch_code_hashes=False
):
    """Return information of the job."""
    try:
        provider = cfg.w3.toChecksumAddress(provider)
        try:
            job, received, job_owner, data_transfer_in, data_transfer_out = self._get_job_info(
                provider, job_key, int(index), int(job_id)
            )
        except Exception as e:
            if str(e) == "VM execution error: Bad instruction fe":
                raise QuietExit("Not valid <provider_address, [m]job_key[/m] and [m]index[/m]> is given") from e

            raise e

        job_prices = self._get_provider_fees_for_job(provider, job_key, int(index))
        if is_print:
            fn = self.EBB_SCRIPTS / "get_job_info.py"
            log(
                f"[green]$[/green] {fn} {provider} {job_key} {index} {job_id} {received_bn}",
                h=False,
                is_code=True,
            )

        self.job_info = {
            "provider": provider,
            "job_owner": job_owner.lower(),
            "job_key": job_key,
            "index": index,
            "availableCore": job_prices[0],
            "cacheType": None,
            "stateCode": job[0],
            "start_timestamp": job[1],
            "submitJob_received_job_price": 0,
            "data_transfer_in_input": None,
            "data_transfer_out_input": None,
            "data_transfer_in": data_transfer_in,
            "data_transfer_out": data_transfer_out,
            "commitment_block_duration": job_prices[1],
            "price_core_min": job_prices[2],
            "price_data_transfer": job_prices[3],
            "price_storage": job_prices[4],
            "price_cache": job_prices[5],
            "received_bn": received_bn,
            "core": None,
            "received": None,
            "run_time": None,
            "actual_elapsed_time": None,
            "cloudStorageID": None,
            "result_ipfs_hash": "",
            "refunded_cent": None,
            "received_cent": None,
            "code_hashes": None,
            "data_transfer_in_to_download": None,
            "data_transfer_out_used": None,
            "storage_duration": None,
            "submitJob_block_hash": None,
            "submitJob_tx_hash": None,
            "data_prices_set_block_numbers": None,
            "submitJob_gas_used": 0,
            "submitJob_LogDataStorageRequest": [],
            "processPayment_block_hash": None,
            "processPayment_tx_hash": None,
            "processPayment_bn": 0,
            "processPayment_gas_used": 0,
            "processPayment_inputs": None,
            "processPayment_dataTransferIn_input": None,
            "processPayment_dataTransferOut_input": None,
            "processPayment_elapsedTime_input": None,
        }
        received_bn = self.update_job_cores(provider, job_key, index, received_bn)
        if not received_bn or received_bn == self.deployed_block_number:
            # First reading from the mongoDB, this will increase the speed to fetch from the logged data
            received_bn_temp = self.mongo_broker.get_job_bn(self.job_info["job_owner"], job_key, index)
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
                self.job_info.update({"received_cent": logged_receipt.args["receivedCent"]})
                self.job_info.update({"refunded_cent": logged_receipt.args["refundedCent"]})
                self.job_info.update({"data_transfer_in_to_download": logged_receipt.args["dataTransferIn"]})
                self.job_info.update({"data_transfer_out_used": logged_receipt.args["dataTransferOut"]})
                self.job_info.update({"actual_elapsed_time": logged_receipt.args["elapsedTime"]})
                self.job_info.update({"processPayment_tx_hash": logged_receipt["transactionHash"].hex()})
                self.job_info.update({"processPayment_bn": logged_receipt["blockNumber"]})
                if self.job_info["result_ipfs_hash"] == empty_bytes32:
                    self.job_info.update({"result_ipfs_hash": b""})

                self.job_info.update({"processPayment_block_hash": logged_receipt["blockHash"].hex()})
                tx_receipt = Ebb.get_transaction_receipt(self.job_info["processPayment_tx_hash"])
                self.job_info.update({"processPayment_gas_used": int(tx_receipt["gasUsed"])})
                #
                tx_by_block = Ebb.get_transaction_by_block(
                    tx_receipt["blockHash"].hex(), tx_receipt["transactionIndex"]
                )
                #: fetching input arguments of the processPayment
                output = Ebb.eBlocBroker.decode_input(tx_by_block["input"])
                self.job_info.update({"processPayment_inputs": output[1][1]})
                self.job_info.update({"processPayment_dataTransferIn_input": output[1][1][3]})
                self.job_info.update({"processPayment_dataTransferOut_input": output[1][1][4]})
                self.job_info.update({"processPayment_elapsedTime_input": output[1][1][5]})
                break
    except Exception as e:
        raise e

    for _core in self.job_info["core"]:
        if float(_core) == 0:
            raise Exception("Failed to get_job_info: Out of index")

    if is_log_print:
        self.get_job_info_print(provider, job_key, index, received_bn)
        if self.job_info["result_ipfs_hash"] == b"":
            del self.job_info["result_ipfs_hash"]

        log(self.job_info)
    elif is_fetch_code_hashes:
        self.get_job_info_print(provider, job_key, index, received_bn, is_print=is_print)

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
        log("E: Provide <[m]provider[/m], [m]job_key[/m], [m]index[/m], and [m]job_id[/m]> as arguments", h=False)
        # ./get_job_info.py 0x29e613b04125c16db3f3613563bfdd0ba24cb629 QmeHL7LvHwQs4xrzPqvkA8fH9T8XGya7BgiLKWb7XG6w71 0
        sys.exit(1)

    Ebb.get_job_info(provider, job_key, index, job_id, received_bn, is_log_print=True)


if __name__ == "__main__":
    try:
        main()
    except QuietExit as e:
        log(f"E: [g]{e}")
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception as e:
        print_tb(e)
