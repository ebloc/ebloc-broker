#!/usr/bin/env python3

import decimal
import os
import sys
from ast import literal_eval as make_tuple
from contextlib import suppress
from pathlib import Path
from typing import Dict, List  # noqa

from broker import cfg, config
from broker._utils._log import console_ruler
from broker._utils.tools import _exit, _remove, log, print_tb
from broker._utils.web3_tools import get_tx_status
from broker._utils.yaml import Yaml
from broker.config import env
from broker.eblocbroker_scripts.bloxber_calls import call
from broker.eblocbroker_scripts.data import is_data_registered
from broker.eblocbroker_scripts.utils import Cent
from broker.errors import QuietExit
from broker.lib import calculate_size
from broker.libs import _git
from broker.utils import (
    CACHE_TYPES,
    CacheID,
    STORAGE_IDs,
    StorageID,
    bytes32_to_ipfs,
    empty_bytes32,
    is_geth_account_locked,
    run,
)

b_open = "[bold]{[/bold]"
b_close = "[bold]}[/bold]"
straight_line = "[green]│[/green]"


class DataStorage:
    """Data strage class."""

    def __init__(self, args) -> None:
        """Create a new Data Stroge object."""
        self.received_block: int = args[0]
        self.storage_duration: int = args[1]
        self.is_private: bool = args[2]
        self.is_verified_used: bool = args[3]
        self.received_deposit: int = 0


class Job:
    """Object for the job that will be submitted."""

    def __init__(self, **kwargs) -> None:
        self.cfg = None
        self.Ebb = cfg.Ebb
        self.w3 = self.Ebb.w3
        self.run_time: List[int] = []
        self.folders_to_share: List[str] = []  # path of folder to share
        self.code_hashes: List[bytes] = []
        self.code_hashes_str: List[str] = []
        self.storage_hours: List[int] = []
        self.storage_ids: List[int] = []
        self.cache_types: List[int] = []
        self.cores: List[int] = []
        self.key = ""
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
        self.price = 0
        self.registered_data_cost = 0
        self.registered_data_cost_list = {}
        self.data_transfer_ins = []
        self.registered_data_files = []
        self.paths = []
        self.data_prices_set_block_numbers = []
        self.data_paths = []
        self.source_code_path = None
        called_fn = os.path.basename(sys._getframe(1).f_code.co_filename)
        if called_fn.startswith("test_"):
            self.is_brownie = True
        else:
            self.is_brownie = False

        for key, value in kwargs.items():
            setattr(self, key, value)

    def cost(self, provider, requester, is_verbose=False, is_ruler=True):
        """Calcualte cost related to the given job."""
        self.provider = provider
        self.requester = requester
        self.check()
        if is_verbose:
            log(f"* Entered into the cost calculation for provider={provider}")

        jp = JobPrices(self)
        jp.set_computational_cost()
        jp.set_storage_cost(is_verbose)
        jp.set_job_price(is_verbose)
        if is_verbose and is_ruler:
            console_ruler(character="-=", style="yellow")

        return jp.job_price, jp.cost

    def analyze_tx_status(self, tx_hash) -> bool:
        try:
            tx_receipt = get_tx_status(tx_hash)
            try:
                if not self.Ebb:
                    log("warning: self.Ebb is an empty object")

                logs = self.Ebb.eBlocBroker.events.LogJob().processReceipt(tx_receipt, errors=self.w3.DISCARD)
                log(vars(logs[0].args))
                log(f"==> job_index={logs[0].args['index']}")
            except IndexError:
                log("E: Transaction is reverted")

            return True
        except Exception as e:
            print_tb(e)
            return False

    def check(self):
        try:
            assert len(self.cores) == len(self.run_time)
            assert len(self.code_hashes) == len(self.storage_hours)
            assert len(self.storage_hours) == len(self.storage_ids)
            assert len(self.cache_types) == len(self.storage_ids)
            for idx, storage_id in enumerate(self.storage_ids):
                assert storage_id <= 4
                if storage_id == StorageID.IPFS:
                    assert self.cache_types[idx] == CacheID.PUBLIC
        except Exception as e:
            print_tb(e)
            raise e

        for idx, code_hash in enumerate(self.code_hashes):
            if self.data_prices_set_block_numbers[idx] > 0 or self.storage_ids[idx] == StorageID.NONE:
                registered_data_bn_list = self.Ebb.get_registered_data_bn(self.provider, code_hash)
                try:
                    registered_data_bn_list[-1]
                except Exception as e:
                    # requested data-file may not registered in the provider
                    raise QuietExit from e

    def set_cache_types(self, types) -> None:
        self.cache_types = types
        for idx, storage_id in enumerate(self.storage_ids):
            if storage_id == StorageID.IPFS_GPG:
                self.cache_types[idx] = CacheID.PRIVATE

    def generate_git_repos(self):
        _git.generate_git_repo(self.folders_to_share)

    def clean_before_submit(self):
        for folder in self.folders_to_share:
            if isinstance(folder, str):
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
                    try:
                        log(f"E: Requester({_from})'s orcid: {orcid.decode('UTF')} is not verified")
                    except:
                        log(f"E: Requester({_from})'s orcid: {orcid} is not verified")
                else:
                    log(f"E: Requester({_from})'s orcid is not registered")

                raise QuietExit
        except QuietExit:
            sys.exit(1)
        except Exception as e:
            print_tb(e)
            sys.exit(1)

    def set_config(self, fn):
        if not os.path.isfile(fn):
            log(f"E: {fn} file does not exist")
            raise QuietExit

        self.cfg = Yaml(fn)
        if "requester_address" in self.cfg["config"] and self.cfg["config"]["requester_address"]:
            self.requester_addr = self.cfg["config"]["requester_address"]
        else:
            log(f"==> requester_address={env.PROVIDER_ID}")
            self.requester_addr = env.PROVIDER_ID

        self.provider_addr = self.cfg["config"]["provider_address"]
        if "search_cheapest_provider" in self.cfg["config"]:
            self.search_cheapest_provider = self.cfg["config"]["search_cheapest_provider"]
        else:
            self.search_cheapest_provider = True

        # self.gmail = self.cfg["config"]["provider_address"]
        self.source_code_storage_id = storage_id = self.cfg["config"]["source_code"]["storage_id"]
        self.storage_ids.append(STORAGE_IDs[storage_id])
        if storage_id == StorageID.NONE:
            self.add_empty_data_item()
        else:
            cache_type = self.cfg["config"]["source_code"]["cache_type"]
            self.cache_types.append(CACHE_TYPES[cache_type])
            self.source_code_path = Path(os.path.expanduser(self.cfg["config"]["source_code"]["path"]))
            size_mb = calculate_size(self.source_code_path)
            self.paths.append(self.source_code_path)
            self.data_transfer_ins.append(size_mb)
            self.storage_hours.append(self.cfg["config"]["source_code"]["storage_hours"])
            self.data_prices_set_block_numbers.append(0)

        # data files are re-ordered, if a registered data is requested from
        # provider(StorageID.NONE) they are added to end of list. This will help
        # during patching for the data files ignoring data files with storage_id
        # None at the end of list
        if "data" in self.cfg["config"]:
            duplicate_path_check = {}
            data_file_keys = []
            for data_key in reversed(self.cfg["config"]["data"]):
                if "path" in self.cfg["config"]["data"][data_key]:
                    _path = self.cfg["config"]["data"][data_key]["path"]
                    with suppress(Exception):
                        if duplicate_path_check[_path]:
                            _exit(f"E: {_path} exists as duplicate item")

                    duplicate_path_check[_path] = True
                if "hash" in self.cfg["config"]["data"][data_key]:
                    data_file_keys.append(data_key)
                    if "storage_id" not in self.cfg["config"]["data"][data_key]:
                        storage_id = StorageID.NONE
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
                    d = data_hash.decode("utf-8")
                    raise QuietExit(f"Requested data={d} is not registered into the provider={self.provider_addr}.")

        self.cores = []
        self.run_time = []
        for key in self.cfg["config"]["jobs"]:
            self.cores.append(self.cfg["config"]["jobs"][key]["cores"])
            self.run_time.append(self.cfg["config"]["jobs"][key]["run_time"])

        self.data_transfer_out = self.cfg["config"]["data_transfer_out"]
        if self.source_code_path:
            self.tmp_dir = self.source_code_path.parent.absolute()
        else:
            self.tmp_dir = Path(os.path.expanduser(self.cfg["config"]["tmp_dir"]))

        self.set_cache_types(self.cache_types)

    def add_empty_data_item(self):
        """Set registered data info as [None, or 0] for other variables."""
        self.cache_types.append(0)
        self.storage_hours.append(0)
        self.storage_ids.append(StorageID.NONE)
        self.data_transfer_ins.append(0)
        self.data_prices_set_block_numbers.append(0)

    def print_before_submit(self):
        for idx, code_hash in enumerate(self.code_hashes_str):
            if StorageID(self.storage_ids[idx]).name == "NONE":
                log(
                    dict(
                        {
                            "code_hash": code_hash,
                            "storage_ids": StorageID(self.storage_ids[idx]).name,
                        }
                    )
                )
            else:
                log(
                    dict(
                        {
                            "path": self.paths[idx],
                            "code_hash": code_hash,
                            "folder_size_mb": self.data_transfer_ins[idx],
                            "storage_ids": StorageID(self.storage_ids[idx]).name,
                            "cache_type": CacheID(self.cache_types[idx]).name,
                        }
                    )
                )

    def _search_best_provider(self, requester, is_verbose=False):
        selected_provider = None
        selected_price = 0
        price_to_select = sys.maxsize
        price_list = []
        if cfg.TEST_PROVIDERS:
            providers_list = cfg.TEST_PROVIDERS  # only wanted providers are looked into
        else:
            providers_list = self.Ebb.get_providers()

        for provider in providers_list:
            try:
                _price, *_ = self.cost(provider, requester, is_verbose)
                price_list.append(_price)
                print()
                # log(f" * provider={provider} | price={Cent(_price)._to()} usd")
                if _price < price_to_select:
                    price_to_select = _price
                    selected_provider = provider
                    selected_price = _price
            except QuietExit:
                pass
            except Exception as e:
                print_tb(e)

        is_all_equal = all(x == price_list[0] for x in price_list)
        return selected_provider, selected_price, is_all_equal

    def search_best_provider(self, requester, is_verbose=True, is_force=False):
        # is_verbose = False
        if not is_force or not self.provider_addr:
            provider_to_share, best_price, is_all_equal = self._search_best_provider(requester, is_verbose=is_verbose)
        else:  #: instead force the given provider address from `self.provider_addr`
            _price, *_ = self.cost(self.provider_addr, requester, is_verbose=True)
            best_price = _price
            is_all_equal = True
            provider_to_share = self.provider_addr

        self.price, *_ = self.cost(provider_to_share, requester)
        if self.price != best_price:
            raise Exception(f"job_price={self.price} and best_price={best_price} does not match")

        if is_all_equal:  # force to submit given provider address
            provider_to_share = self.Ebb.w3.toChecksumAddress(self.provider_addr)

        log(f"[g]##[/g] provider_to_share={provider_to_share} | best_price={Cent(best_price)._to()} [blue]usd")
        return self.Ebb.w3.toChecksumAddress(provider_to_share)

    def get_generated_output_files(self):
        pass


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
        self.registered_data_cost_list = {}
        self.registered_data_cost = 0

    def set_provider_info(self):
        """Set provider info into variables."""
        if cfg.IS_BROWNIE_TEST:
            self.Ebb.eBlocBroker = config.ebb
            *_, provider_prices = self.Ebb._get_provider_info(self.job.provider)
        else:
            if self.Ebb.does_provider_exist(self.job.provider):
                *_, provider_prices = self.Ebb._get_provider_info(self.job.provider)
            else:
                log(f"E: {self.job.provider} does not exist as a provider")
                raise QuietExit

        self.price_core_min = provider_prices[2]
        self.price_data_transfer = provider_prices[3]
        self.price_storage = provider_prices[4]
        self.price_cache = provider_prices[5]

    def set_computational_cost(self):
        """Set computational cost within the object."""
        self.computational_cost = 0
        for idx, core in enumerate(self.job.cores):
            self.computational_cost += int(self.price_core_min * core * self.job.run_time[idx])

    def new_contract_function_call(self, code_hash):
        """Call contract function with new brownie object.

        This part is not needed when `{from: }` is removed from the getter in the smart contract
        """
        data = ("func", self.job.provider, self.job.requester, code_hash)
        fn = call.__file__
        output = run(["python", fn, *[str(arg) for arg in data]])  # GOTCHA
        output = output.split("\n")
        received_deposit = float(output[0])
        data_storage_duration = make_tuple(output[1])
        return received_deposit, data_storage_duration

    def create_data_storage(self, code_hash: str, is_main=True):
        """Create data storage object."""
        if self.is_brownie or is_main:
            received_deposit, job_storage_duration = self.Ebb.get_job_storage_duration(
                self.job.provider, self.job.requester, code_hash
            )
        else:
            received_deposit, job_storage_duration = self.new_contract_function_call(code_hash)

        ds = DataStorage(job_storage_duration)
        ds.received_deposit = received_deposit
        return ds

    def set_storage_cost(self, is_verbose=False):
        """Calculate the cache cost."""
        self.registered_data_cost_list = {}
        #: for logging purpose
        self.registered_data_cost_list_usd = {}
        self.registered_data_cost = 0
        self.storage_cost = 0
        self.cache_cost = 0
        self.data_transfer_in_sum = 0
        bn = self.Ebb.get_block_number()
        #: pre-check set zero if extra data-transfer-in is given
        for idx, code_hash in enumerate(self.job.code_hashes):
            if self.job.storage_ids[idx] == StorageID.NONE:
                self.job.data_transfer_ins[idx] = 0

        _is_private_dict = {}
        for idx, code_hash in enumerate(self.job.code_hashes):
            if self.is_brownie:
                ds = self.create_data_storage(code_hash)
            else:
                ds = self.create_data_storage(self.job.code_hashes_str[idx])

            if ds.received_block + ds.storage_duration < self.w3.eth.block_number:
                # storage duration is completed
                ds.received_deposit = 0

            try:
                _code_hash = code_hash.decode("utf-8")
            except:
                _code_hash = bytes32_to_ipfs(code_hash, is_verbose=False)

            if is_verbose and _code_hash:
                _is_private_dict[_code_hash] = ds.is_private

            if idx == len(self.job.code_hashes) - 1 and _is_private_dict:
                log("[pink]**[/pink] is_private=", end="")
                log(_is_private_dict)

            # print(received_block + storage_duration >= self.w3.eth.block_number)
            # if ds.received_deposit > 0 or
            if (ds.received_deposit > 0 and ds.received_block + ds.storage_duration >= self.w3.eth.block_number) or (
                ds.received_block + ds.storage_duration >= self.w3.eth.block_number
                and not ds.is_private
                and ds.is_verified_used
            ):
                if is_verbose:
                    log(f"** for {bytes32_to_ipfs(code_hash)} cost of storage is not paid")
            elif self.job.data_prices_set_block_numbers[idx] > 0 or self.job.storage_ids[idx] == StorageID.NONE:
                if self.job.data_prices_set_block_numbers[idx] == 0:
                    registered_data_bn_list = self.Ebb.get_registered_data_bn(self.job.provider, code_hash)
                    if bn > registered_data_bn_list[-1]:
                        data_fee_set_bn = registered_data_bn_list[-1]
                    else:
                        data_fee_set_bn = registered_data_bn_list[-2]
                else:
                    data_fee_set_bn = self.job.data_prices_set_block_numbers[idx]

                # if true, registered data's price should be considered for storage
                (data_price, *_) = self.Ebb.get_registered_data_price(
                    self.job.provider,
                    code_hash,
                    data_fee_set_bn,
                )
                self.storage_cost += data_price
                self.registered_data_cost_list[_code_hash] = data_price
                self.registered_data_cost_list_usd[_code_hash] = self.to_usd(data_price, is_color=False)
                self.registered_data_cost += data_price
            elif not ds.received_deposit:  # and (received_block + storage_duration < w3.eth.block_number)
                self.data_transfer_in_sum += self.job.data_transfer_ins[idx]
                if self.job.storage_hours[idx] > 0:
                    self.storage_cost += (
                        self.price_storage * self.job.data_transfer_ins[idx] * self.job.storage_hours[idx]
                    )
                else:
                    self.cache_cost += self.price_cache * self.job.data_transfer_ins[idx]

        self.data_transfer_in_cost = self.data_transfer_in_sum * self.price_data_transfer
        self.data_transfer_out_cost = self.job.data_transfer_out * self.price_data_transfer
        self.data_transfer_cost = self.data_transfer_in_cost + self.data_transfer_out_cost

    def to_usd(self, amount, is_color=True) -> str:
        if is_color:
            _amount = str(decimal.Decimal(Cent(amount)._to()))[:8]
            return f"{_amount} [blue]usd"
        else:
            return f"{Cent(amount)._to()} usd"

    def set_job_price(self, is_verbose=False) -> None:
        """Set job price in the object."""
        self.job_price = self.computational_cost + self.data_transfer_cost + self.cache_cost + self.storage_cost
        self.cost["computational"] = self.computational_cost
        self.cost["cache"] = self.cache_cost
        self.cost["storage"] = self.storage_cost
        self.cost["data_transfer_in"] = self.data_transfer_in_cost
        self.cost["data_transfer_out"] = self.data_transfer_out_cost
        self.cost["data_transfer"] = self.data_transfer_cost
        if is_verbose:
            log(f"** price_core_min={self.to_usd(self.price_core_min)}")
            log(f"** price_data_transfer={self.to_usd(self.price_data_transfer)}")
            log(f"** price_storage={self.to_usd(self.price_storage)}")
            log(f"** price_cache={self.to_usd(self.price_cache)}")
            log(f"{b_open}")
            log(f"{straight_line} job_price={Cent(self.job_price)._to()} usd for provider={self.job.provider}")
            c1 = f"{straight_line}       [yellow]*[/yellow]"
            for k, v in self.cost.items():
                if k not in ("data_transfer_out", "data_transfer_in"):
                    log(f"{straight_line}   * {k}={self.to_usd(v)}")
                    if k == "storage":
                        log(f"{c1} in={self.to_usd(self.cost['data_transfer_in'])}")
                        if self.registered_data_cost > 0:
                            log(f"{c1} registered_data={self.to_usd(self.registered_data_cost)}")
                            log(f"{straight_line}         {self.registered_data_cost_list_usd}")

                if k == "data_transfer":
                    log(f"{c1} in={self.to_usd(self.cost['data_transfer_in'])}")
                    log(f"{c1} out={self.to_usd(self.cost['data_transfer_out'])}")

            log(f"{b_close}")
        elif self.registered_data_cost_list:
            log(self.registered_data_cost_list)
