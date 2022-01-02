#!/usr/bin/env python3

import os
import sys
from ast import literal_eval as make_tuple
from contextlib import suppress
from pathlib import Path
from typing import Dict, List

from broker import cfg
from broker._utils._log import br
from broker._utils.tools import _exit, _remove, log, print_tb
from broker._utils.web3_tools import get_tx_status
from broker._utils.yaml import Yaml
from broker.config import env
from broker.eblocbroker_scripts.bloxber_calls import call
from broker.eblocbroker_scripts.data import is_data_registered
from broker.errors import QuietExit
from broker.lib import calculate_size
from broker.libs import _git
from broker.utils import (
    CACHE_TYPES,
    CacheType,
    STORAGE_IDs,
    StorageID,
    bytes32_to_ipfs,
    empty_bytes32,
    is_geth_account_locked,
    run,
)


class DataStorage:
    """Data strage class."""

    def __init__(self, args) -> None:
        """Create a new Data Stroge object."""
        self.received_block = args[0]
        self.storage_duration = args[1]
        self.is_private = args[2]
        self.is_verified_used = args[3]
        self.received_storage_deposit: int = 0


class Job:
    """Object for the job that will be submitted."""

    def __init__(self, **kwargs) -> None:
        self.cfg = None
        self.Ebb = cfg.Ebb
        self.w3 = self.Ebb.w3
        self.run_time: List[int] = []
        self.folders_to_share: List[str] = []  # path of folder to share
        self.source_code_hashes: List[bytes] = []
        self.source_code_hashes_str: List[str] = []
        self.storage_hours: List[int] = []
        self.storage_ids: List[int] = []
        self.cache_types: List[int] = []
        self.cores: List[int] = []
        self.run_time = []
        self.keys = {}  # type: Dict[str, str]
        self.keys_final = {}  # type: Dict[str, str]
        self.foldername_tar_hash = {}  # type: Dict[str, str]
        self.tar_hashes = {}  # type: Dict[str, str]
        self.source_code_storage_id: str = ""
        self.tmp_dir = Path("")
        self.provider = ""
        self.requester = ""
        self._id = None  # must be set 0 or greater than 0 values
        self.requester_addr: str = ""
        self.provider_addr: str = ""
        self.is_registered_data_requested = {}  # type: Dict[str, bool]
        self.data_transfer_out: int = 0
        self.data_transfer_ins = []
        self.registered_data_files = []
        self.paths = []
        self.data_prices_set_block_numbers = []
        self.data_paths = []
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
                if not self.Ebb:
                    log("Warning: self.Ebb is empty object")

                processed_logs = self.Ebb.eBlocBroker.events.LogJob().processReceipt(tx_receipt, errors=self.w3.DISCARD)
                log(vars(processed_logs[0].args))
                log(f"==> job_index={processed_logs[0].args['index']}")
            except IndexError:
                log("E: Transaction is reverted")
            return True
        except Exception as e:
            print_tb(e)
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
            print_tb(e)
            raise e

    def set_cache_types(self, types) -> None:
        self.cache_types = types
        for idx, storage_id in enumerate(self.storage_ids):
            if storage_id == StorageID.IPFS_GPG:
                self.cache_types[idx] = CacheType.PRIVATE

    def generate_git_repos(self):
        _git.generate_git_repo(self.folders_to_share)

    def clean_before_submit(self):
        for folder in self.folders_to_share:
            if not isinstance(folder, bytes):
                _remove(os.path.join(folder, ".mypy_cache"))

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
            print_tb()
            sys.exit(1)

    def set_config(self, fn):
        if not os.path.isfile(fn):
            log(f"E: {fn} file does not exist")
            raise QuietExit

        self.cfg = Yaml(fn)
        self.requester_addr = self.cfg["config"]["requester_address"]
        self.provider_addr = self.cfg["config"]["provider_address"]
        self.source_code_storage_id = storage_id = self.cfg["config"]["source_code"]["storage_id"]
        self.storage_ids.append(STORAGE_IDs[storage_id])
        if storage_id == StorageID.NONE:
            self.add_empty_data_item()
        else:
            cache_type = self.cfg["config"]["source_code"]["cache_type"]
            self.cache_types.append(CACHE_TYPES[cache_type])
            source_code_path = Path(os.path.expanduser(self.cfg["config"]["source_code"]["path"]))
            size_mb = calculate_size(source_code_path)
            self.paths.append(source_code_path)
            self.data_transfer_ins.append(size_mb)
            self.storage_hours.append(self.cfg["config"]["source_code"]["storage_hours"])
            self.data_prices_set_block_numbers.append(0)

        duplicate_path_check = {}
        data_file_keys = []
        # data files are re-ordered, if a registered data is requested from
        # provider(StorageID.NONE) they are added to end of list. This will help
        # during patching for the data files ignoring data files with storage_id
        # None at the end of list
        for data_key in reversed(self.cfg["config"]["data"]):
            if "path" in self.cfg["config"]["data"][data_key]:
                _path = self.cfg["config"]["data"][data_key]["path"]
                with suppress(Exception):
                    if duplicate_path_check[_path]:
                        _exit(f"E: {_path} exists as duplicate item")

                duplicate_path_check[_path] = True
            if "hash" in self.cfg["config"]["data"][data_key]:
                data_file_keys.append(data_key)
            else:  # priority given to data that from local folder
                data_file_keys.insert(0, data_key)

        for key in data_file_keys:
            is_data_hash = False
            if "hash" in self.cfg["config"]["data"][key]:
                # process on the registered data of the provider
                data_hash = self.cfg["config"]["data"][key]["hash"]
                if len(data_hash) == 32:
                    data_hash = data_hash.encode()

                self.paths.append(data_hash)
                self.registered_data_files.append(data_hash)
                self.add_empty_data_item()
                self.is_registered_data_requested[data_hash] = True
                is_data_hash = True
            else:
                storage_id = self.cfg["config"]["data"][key]["storage_id"]
                self.storage_ids.append(STORAGE_IDs[storage_id])
                if storage_id == StorageID.NONE:
                    self.add_empty_data_item()
                else:
                    cache_type = self.cfg["config"]["data"][key]["cache_type"]
                    self.cache_types.append(CACHE_TYPES[cache_type])
                    path = Path(os.path.expanduser(self.cfg["config"]["data"][key]["path"]))
                    size_mb = calculate_size(path)
                    self.paths.append(path)
                    self.data_paths.append(path)
                    self.data_transfer_ins.append(size_mb)
                    self.storage_hours.append(self.cfg["config"]["data"][key]["storage_hours"])
                    self.data_prices_set_block_numbers.append(0)

            if is_data_hash and not is_data_registered(self.provider_addr, data_hash):
                self.cfg.remove_temp()
                raise Exception(f"## requested({data_hash}) data is not registered into provider")

        self.cores = []
        self.run_time = []
        for key in self.cfg["config"]["jobs"]:
            self.cores.append(self.cfg["config"]["jobs"][key]["cores"])
            self.run_time.append(self.cfg["config"]["jobs"][key]["run_time"])

        self.data_transfer_out = self.cfg["config"]["data_transfer_out"]
        if source_code_path:
            self.tmp_dir = source_code_path.parent.absolute()
        else:
            self.tmp_dir = Path(os.path.expanduser(self.cfg["config"]["tmp_dir"]))

        self.set_cache_types(self.cache_types)
        self.cfg.remove_temp()

    def add_empty_data_item(self):
        """Set registered data info as empty value for other variables."""
        self.cache_types.append(0)
        self.storage_hours.append(0)
        self.storage_ids.append(StorageID.NONE)
        self.data_transfer_ins.append(0)
        self.data_prices_set_block_numbers.append(0)  # TODO: calculate from the contract

    def print_before_submit(self):
        for idx, source_code_hash in enumerate(self.source_code_hashes_str):
            print_temp = {
                "path": self.paths[idx],
                "source_code_hash": source_code_hash,
                "folder_size_mb": self.data_transfer_ins[idx],
                "storage_ids": StorageID(self.storage_ids[idx]).name,
                "cache_type": CacheType(self.cache_types[idx]).name,
            }
            log(print_temp)
            log()


class JobPrices:
    """Calcualte job prices for the related provider."""

    def __init__(self, job):
        self.Ebb = cfg.Ebb
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
        self.data_transfer_in_cost: int = 0
        self.data_transfer_out_cost: int = 0

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
            job_storage_time = self.Ebb.get_job_storage_time(self.job.provider, source_code_hash)
        else:
            filename = call.__file__
            data = ("func", self.job.provider, self.job.requester, source_code_hash)
            output = run(["python", filename, *[str(arg) for arg in data]])  ###
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

            if ds.received_block + ds.storage_duration < self.w3.eth.block_number:
                # storage time is completed
                ds.received_storage_deposit = 0

            try:
                _source_code_hash = source_code_hash.decode("utf-8")
            except:
                _source_code_hash = bytes32_to_ipfs(source_code_hash)

            log(f"==> is_private{br(_source_code_hash, 'blue')}={ds.is_private}")
            # print(received_block + storage_duration >= self.w3.eth.block_number)
            # if ds.received_storage_deposit > 0 or
            if (
                ds.received_storage_deposit > 0 and ds.received_block + ds.storage_duration >= self.w3.eth.block_number
            ) or (
                ds.received_block + ds.storage_duration >= self.w3.eth.block_number
                and not ds.is_private
                and ds.is_verified_used
            ):
                log(f"==> For {bytes32_to_ipfs(source_code_hash)} cost of storage is not paid")
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

                #  if not ds.received_storage_deposit and (received_block + storage_duration < w3.eth.block_number):
                if not ds.received_storage_deposit:
                    self.data_transfer_in_sum += self.job.data_transfer_ins[idx]
                    if self.job.storage_hours[idx] > 0:
                        self.storage_cost += (
                            self.price_storage * self.job.data_transfer_ins[idx] * self.job.storage_hours[idx]
                        )
                    else:
                        self.cache_cost += self.price_cache * self.job.data_transfer_ins[idx]

        self.data_transfer_in_cost = self.price_data_transfer * self.data_transfer_in_sum
        self.data_transfer_out_cost = self.price_data_transfer * self.job.data_transfer_out
        self.data_transfer_cost = self.data_transfer_in_cost + self.data_transfer_out_cost

    def set_job_price(self):
        """Set job price in the object."""
        self.job_price = self.computational_cost + self.data_transfer_cost + self.cache_cost + self.storage_cost
        log(f"==> price_core_min={self.price_core_min}")
        log(f"==> price_data_transfer={self.price_data_transfer}")
        log(f"==> price_storage={self.price_storage}")
        log(f"==> price_cache={self.price_cache}")
        log(f" * job_price={self.job_price}", "bold blue")
        self.cost["computational"] = self.computational_cost
        self.cost["cache"] = self.cache_cost
        self.cost["storage"] = self.storage_cost
        self.cost["data_transfer_in"] = self.data_transfer_in_cost
        self.cost["data_transfer_out"] = self.data_transfer_out_cost
        self.cost["data_transfer"] = self.data_transfer_cost
        for key, value in self.cost.items():
            if key not in ("data_transfer_out", "data_transfer_in"):
                log(f"\t[bold blue]==> {key}={value}")

            if key == "data_transfer":
                log(f"\t\t[bold yellow]==> in={self.cost['data_transfer_in']}")
                log(f"\t\t[bold yellow]==> out={self.cost['data_transfer_out']}")
