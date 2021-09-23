#!/usr/bin/env python3

import os
import sys
from ast import literal_eval as make_tuple
from pprint import pprint
from typing import Dict, List

import broker.eblocbroker.Contract as Contract
import broker.libs.git as git
from broker._utils.tools import QuietExit, _colorize_traceback, log
from broker.config import env
from broker.eblocbroker.bloxber_calls import call
from broker.lib import get_tx_status
from broker.utils import (
    CacheType,
    StorageID,
    bytes32_to_ipfs,
    empty_bytes32,
    is_geth_account_locked,
    run,
    silent_remove,
)


class DataStorage:
    """Data strage class."""

    def __init__(self, args) -> None:
        """Create a new Data Stroge object."""
        self.received_block = args[0]
        self.storage_duration = args[1]
        self.is_private = args[2]
        self.is_verified_used = args[3]
        self.received_storage_deposit = 0


class Job:
    """Object for the job that will be submitted."""

    def __init__(self, **kwargs) -> None:
        self.Ebb = Contract.ebb()
        self.run_time: List[int] = []
        self.folders_to_share: List[str] = []  # path of folder to share
        self.source_code_hashes: List[bytes] = []
        self.source_code_hashes_str: List[str] = []
        self.storage_hours: List[int] = []
        self.storage_ids: List[int] = []
        self.cache_types: List[int] = []
        self.run_time = []
        self.keys = {}  # type: Dict[str, str]
        self.foldername_tar_hash = {}  # type: Dict[str, str]
        self.tar_hashes = {}  # type: Dict[str, str]
        self.base_dir = ""
        self._id = None  # must be set 0 or greater than 0 values
        called_filename = os.path.basename(sys._getframe(1).f_code.co_filename)
        if called_filename.startswith("test_"):
            self.is_brownie = True
        else:
            self.is_brownie = False

        for key, value in kwargs.items():
            setattr(self, key, value)

    def cost(self, provider, requester):
        """Calcualte cost related to the given job."""
        log("==> Entered into the cost calculation...")
        self.provider = provider
        self.requester = requester
        self.check()

        jp = JobPrices(self)
        jp.set_computational_cost()
        jp.set_storage_cost()  # burda patliyor sanki DELETE
        jp.set_job_price()
        return jp.job_price, jp.cost

    def analyze_tx_status(self, tx_hash) -> bool:
        try:
            tx_receipt = get_tx_status(tx_hash)
            try:
                processed_logs = self.Ebb.eBlocBroker.events.LogJob().processReceipt(tx_receipt, errors=self.w3.DISCARD)
                pprint(vars(processed_logs[0].args))
                log(f"==> job_index={processed_logs[0].args['index']}")
            except IndexError:
                log("E: Transaction is reverted")
            return True
        except Exception as e:
            _colorize_traceback(e)
            return False

    def check(self):
        try:
            assert len(self.cores) == len(self.run_time)
            assert len(self.source_code_hashes) == len(self.storage_hours)
            assert len(self.storage_hours) == len(self.storage_ids)
            assert len(self.cache_types) == len(self.storage_ids)

            for idx, storage_id in enumerate(self.storage_ids):
                assert storage_id <= 4
                if storage_id == StorageID.IPFS:
                    assert self.cache_types[idx] == CacheType.PUBLIC
        except Exception as e:
            _colorize_traceback(e)
            raise e

    def set_cache_types(self, types) -> None:
        self.cache_types = types
        for idx, storage_id in enumerate(self.storage_ids):
            if storage_id == StorageID.IPFS_GPG:
                self.cache_types[idx] = CacheType.PRIVATE

    def generate_git_repos(self):
        git.generate_git_repo(self.folders_to_share)

    def clean_before_submit(self):
        for folder in self.folders_to_share:
            silent_remove(os.path.join(folder, ".mypy_cache"), is_warning=False)

    def check_account_status(self, _from):
        try:
            if isinstance(_from, int):
                _from = self.Ebb.account_id_to_address(_from)

            if not env.IS_BLOXBERG and is_geth_account_locked(_from):
                log(f"E: Account({_from}) is locked")
                raise QuietExit

            if not self.Ebb.does_requester_exist(_from):
                log(f"E: Requester's Ethereum address {_from} is not registered")
                sys.exit(1)

            *_, orcid = self.Ebb.get_requester_info(_from)
            if not self.Ebb.is_orcid_verified(_from):
                if orcid != empty_bytes32:
                    log(f"E: Requester({_from})'s orcid: {orcid.decode('UTF')} is not verified")
                else:
                    log(f"E: Requester({_from})'s orcid is not registered")
                raise QuietExit
        except QuietExit:
            sys.exit(1)
        except:
            _colorize_traceback()
            sys.exit(1)


class JobPrices:
    """Calcualte job prices for the related provider."""

    def __init__(self, job):
        self.Ebb = Contract.ebb()
        self.ebb = self.Ebb.eBlocBroker
        self.w3 = self.Ebb.w3
        self.job = job
        self.is_brownie = job.is_brownie
        self.cost = {}
        self.computational_cost = 0
        self.job_price = 0
        self.cache_cost = 0
        self.storage_cost = 0
        self.data_transfer_in_sum = 0
        self.data_transfer_cost = 0
        self.set_provider_info()

    def set_provider_info(self):
        """Set provider info into variables."""
        if self.Ebb.does_provider_exist(self.job.provider):
            *_, provider_price_info = self.Ebb._get_provider_info(self.job.provider, 0)
        else:
            log(f"E: {self.job.provider} does not exist as a provider")
            raise QuietExit

        self.price_core_min = provider_price_info[2]
        self.price_data_transfer = provider_price_info[3]
        self.price_storage = provider_price_info[4]
        self.price_cache = provider_price_info[5]

    def set_computational_cost(self):
        """Set computational cost in the object."""
        self.computational_cost = 0
        for idx, core in enumerate(self.job.cores):
            self.computational_cost += int(self.price_core_min * core * self.job.run_time[idx])

    def create_data_storage(self, source_code_hash: str):
        """Create data storage object."""
        if self.is_brownie:
            received_storage_deposit = self.Ebb.get_received_storage_deposit(
                self.job.provider, self.job.requester, source_code_hash
            )
            job_storage_time = self.Ebb.get_job_storage_time(
                self.job.provider, source_code_hash, _from=self.job.provider
            )
        else:  #
            filename = call.__file__
            data = ("", self.job.provider, self.job.requester, source_code_hash)
            output = run(["python", filename, *[str(arg) for arg in data]])
            output = output.split("\n")
            received_storage_deposit = float(output[0])
            job_storage_time = make_tuple(output[1])

        ds = DataStorage(job_storage_time)
        ds.received_storage_deposit = received_storage_deposit
        return ds

    def set_storage_cost(self):
        """Calculate the cache cost."""
        self.storage_cost = 0
        self.cache_cost = 0
        self.data_transfer_in_sum = 0
        for idx, source_code_hash in enumerate(self.job.source_code_hashes):
            if self.is_brownie:
                ds = self.create_data_storage(source_code_hash)
            else:
                ds = self.create_data_storage(self.job.source_code_hashes_str[idx])

            if ds.received_block + ds.storage_duration < self.w3.eth.blockNumber:
                # storage time is completed
                ds.received_storage_deposit = 0

            print(f"is_private:{ds.is_private}")
            # print(received_block + storage_duration >= self.w3.eth.blockNumber)
            # if ds.received_storage_deposit > 0 or
            if (
                ds.received_storage_deposit > 0 and ds.received_block + ds.storage_duration >= self.w3.eth.blockNumber
            ) or (
                ds.received_block + ds.storage_duration >= self.w3.eth.blockNumber
                and not ds.is_private
                and ds.is_verified_used
            ):
                print(f"==> For {bytes32_to_ipfs(source_code_hash)} cost of storage is not paid")
            else:
                if self.job.data_prices_set_block_numbers[idx] > 0:
                    # if true, registered data's price should be considered for storage
                    output = self.ebb.getRegisteredDataPrice(
                        self.job.provider,
                        source_code_hash,
                        self.job.data_prices_set_block_numbers[idx],
                    )
                    data_price = output[0]
                    self.storage_cost += data_price
                    break

                #  if not ds.received_storage_deposit and (received_block + storage_duration < w3.eth.blockNumber):
                if not ds.received_storage_deposit:
                    self.data_transfer_in_sum += self.job.data_transfer_ins[idx]
                    if self.job.storage_hours[idx] > 0:
                        self.storage_cost += (
                            self.price_storage * self.job.data_transfer_ins[idx] * self.job.storage_hours[idx]
                        )
                    else:
                        self.cache_cost += self.price_cache * self.job.data_transfer_ins[idx]

        self.data_transfer_in_cost = self.price_data_transfer * self.data_transfer_in_sum
        self.data_transfer_out_cost = self.price_data_transfer * self.job.dataTransferOut
        self.data_transfer_cost = self.data_transfer_in_cost + self.data_transfer_out_cost

    def set_job_price(self):
        """Set job price in the object."""
        self.job_price = self.computational_cost + self.data_transfer_cost + self.cache_cost + self.storage_cost
        log(f"job_price={self.job_price}", "blue")
        self.cost["computational"] = self.computational_cost
        self.cost["cache"] = self.cache_cost
        self.cost["storage"] = self.storage_cost
        self.cost["data_transfer_in"] = self.data_transfer_in_cost
        self.cost["data_transfer_out"] = self.data_transfer_out_cost
        self.cost["data_transfer"] = self.data_transfer_cost
        for key, value in self.cost.items():
            if key == "data_transfer":
                log(
                    f"\t=> {key}={value} <=> [in:{self.cost['data_transfer_in']} out:{self.cost['data_transfer_out']}]",
                    "blue",
                )
            else:
                if key not in ("data_transfer_out", "data_transfer_in"):
                    log(f"\t=> {key}={value}", "blue")
