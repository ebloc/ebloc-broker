#!/usr/bin/env python3

import sys
from os import path, popen
from typing import List

from config import QuietExit
from utils import CacheType, StorageID, _colorize_traceback, bytes32_to_ipfs, empty_bytes32, is_geth_account_locked, log

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))


class DataStorage:
    def __init__(self, Ebb, w3, provider, source_code_hash, is_brownie=False) -> None:
        if is_brownie:
            output = Ebb.getJobStorageTime(provider, source_code_hash)
        else:
            if not w3.isChecksumAddress(provider):
                provider = w3.toChecksumAddress(provider)
            output = Ebb.functions.getJobStorageTime(provider, source_code_hash).call({"from": provider})

        self.received_block = output[0]
        self.storage_duration = output[1]
        self.is_private = output[2]
        self.is_verified_used = output[3]


class Job:
    """Object for the job that will be submitted"""
    def __init__(self, **kwargs) -> None:
        self.execution_durations: List[int] = []
        self.folders_to_share: List[str] = []  # path of folder to share
        self.source_code_hashes: List[bytes] = []
        self.storage_hours: List[int] = []
        self.execution_durations = []
        for key, value in kwargs.items():
            setattr(self, key, value)

    def check(self):
        try:
            assert len(self.cores) == len(self.execution_durations)
            assert len(self.source_code_hashes) == len(self.storage_hours)
            assert len(self.storage_hours) == len(self.storage_ids)
            assert len(self.cache_types) == len(self.storage_ids)

            for idx, storage_id in enumerate(self.storage_ids):
                assert storage_id <= 4
                if storage_id == StorageID.IPFS:
                    assert self.cache_types[idx] == CacheType.PUBLIC
        except:
            _colorize_traceback()
            raise

    def check_account_status(self, account_id):
        import eblocbroker.Contract as Contract
        _Ebb = Contract.eblocbroker
        try:
            _from = _Ebb.account_id_to_address(account_id)
            if is_geth_account_locked(_from):
                log(f"E: Account({_from}) is locked", "red")
                raise QuietExit

            if not _Ebb.eBlocBroker.functions.doesRequesterExist(_from).call():
                log(f"E: Requester's Ethereum address {_from} is not registered", "red")
                sys.exit(1)

            *_, orcid = _Ebb.eBlocBroker.functions.getRequesterInfo(_from).call()
            if not _Ebb.eBlocBroker.functions.isOrcIDVerified(_from).call():
                if orcid != empty_bytes32:
                    log(f"E: Requester({_from})'s orcid: {orcid.decode('UTF')} is not verified", "red")
                else:
                    log(f"E: Requester({_from})'s orcid is not registered", "red")
                raise QuietExit
        except QuietExit:
            sys.exit(1)
        except:
            _colorize_traceback()
            sys.exit(1)


class JobPrices:
    def __init__(self, Ebb, w3, job, msg_sender, is_brownie=False):
        self.Ebb = Ebb
        self.w3 = w3
        self.msg_sender = msg_sender
        self.is_brownie = is_brownie
        self.computational_cost = 0
        self.job_price = 0
        self.cache_cost = 0
        self.storage_cost = 0
        self.data_transfer_in_sum = 0
        self.job_price = 0
        self.cost = dict()
        self.data_transfer_cost = None

        if is_brownie:
            provider_info = Ebb.getProviderInfo(job.provider, 0)
        else:  # real chain
            if Ebb.functions.doesProviderExist(job.provider).call():
                provider_info = Ebb.functions.getProviderInfo(job.provider, 0).call()
            else:
                log(f"E: {job.provider} does not exist as a provider", "red")
                raise QuietExit

        provider_price_info = provider_info[1]
        self.job = job
        self.price_core_min = provider_price_info[2]
        self.price_data_transfer = provider_price_info[3]
        self.price_storage = provider_price_info[4]
        self.price_cache = provider_price_info[5]

    def set_computational_cost(self):
        self.computational_cost = 0
        for idx, core in enumerate(self.job.cores):
            self.computational_cost += int(self.price_core_min * core * self.job.execution_durations[idx])

    def set_storage_cost(self):
        """Calculating the cache cost."""
        self.storage_cost = 0
        self.cache_cost = 0
        data_transfer_in_sum = 0
        for idx, source_code_hash in enumerate(self.job.source_code_hashes):
            ds = DataStorage(self.Ebb, self.w3, self.job.provider, source_code_hash, self.is_brownie)
            if self.is_brownie:
                received_storage_deposit = self.Ebb.getReceivedStorageDeposit(
                    self.job.provider, self.job.requester, source_code_hash
                )
            else:
                received_storage_deposit = self.Ebb.functions.getReceivedStorageDeposit(
                    self.job.provider, self.job.requester, source_code_hash
                ).call({"from": self.msg_sender})

            if ds.received_block + ds.storage_duration < self.w3.eth.blockNumber:
                # storage time is completed
                received_storage_deposit = 0

            print(f"is_private:{ds.is_private}")
            # print(received_block + storage_duration >= self.w3.eth.blockNumber)
            # if received_storage_deposit > 0 or
            if (
                received_storage_deposit > 0 and ds.received_block + ds.storage_duration >= self.w3.eth.blockNumber
            ) or (
                ds.received_block + ds.storage_duration >= self.w3.eth.blockNumber and not ds.is_private and ds.is_verified_used
            ):
                print(f"For {bytes32_to_ipfs(source_code_hash)} cost of storage is not paid")
            else:
                if self.job.data_prices_set_block_numbers[idx] > 0:
                    # if true, registered data's price should be considered for storage
                    output = self.Ebb.getRegisteredDataPrice(
                        self.job.provider, source_code_hash, self.job.data_prices_set_block_numbers[idx],
                    )
                    data_price = output[0]
                    self.storage_cost += data_price
                    break

                #  if not received_storage_deposit and (received_block + storage_duration < w3.eth.blockNumber):
                if not received_storage_deposit:
                    data_transfer_in_sum += self.job.dataTransferIns[idx]
                    if self.job.storage_hours[idx] > 0:
                        self.storage_cost += (
                            self.price_storage * self.job.dataTransferIns[idx] * self.job.storage_hours[idx]
                        )
                    else:
                        self.cache_cost += self.price_cache * self.job.dataTransferIns[idx]
        self.data_transfer_in_cost = self.price_data_transfer * data_transfer_in_sum
        self.data_transfer_out_cost = self.price_data_transfer * self.job.dataTransferOut
        self.data_transfer_cost = self.data_transfer_in_cost + self.data_transfer_out_cost

    def set_job_price(self):
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
                log(f"\t=> {key}={value} <=> [in:{self.cost['data_transfer_in']} out:{self.cost['data_transfer_out']}]", "blue")
            else:
                if key != "data_transfer_out" and key != "data_transfer_in":
                    log(f"\t=> {key}={value}", "blue")


def cost(provider, requester, job, Ebb, w3, is_brownie=False):
    called_filename = path.basename(sys._getframe(1).f_code.co_filename)
    if called_filename.startswith("test_"):
        is_brownie = True

    print("\nEntered into cost calculation...")
    job.provider = provider
    job.requester = requester
    job.check()

    jp = JobPrices(Ebb, w3, job, provider, is_brownie)
    jp.set_computational_cost()
    jp.set_storage_cost()
    jp.set_job_price()
    return jp.job_price, jp.cost


def new_test():
    try:
        *_, columns = popen("stty size", "r").read().split()
    except:
        columns = 20

    line = "-" * int(columns)
    print(f"\x1b[6;30;43m{line}\x1b[0m")
