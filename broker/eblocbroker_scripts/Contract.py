#!/usr/bin/env python3

import re
import subprocess
import sys
import time
from contextlib import suppress
from halo import Halo
from os.path import expanduser
from pymongo import MongoClient
from typing import Union
from web3.exceptions import TransactionNotFound
from web3.types import TxReceipt

from broker import cfg, config
from broker._utils._log import WHERE, ok
from broker._utils.tools import exit_after, log, print_tb, without_keys
from broker._utils.yaml import Yaml
from broker.config import env
from broker.errors import QuietExit, Web3NotConnected
from broker.imports import nc
from broker.libs.mongodb import MongoBroker
from broker.utils import ipfs_to_bytes32, terminate
from brownie import accounts, history
from brownie.network.account import Account, LocalAccount
from brownie.network.transaction import TransactionReceipt

if cfg.NETWORK_ID == "sepolia":
    GAS_PRICE = 5.0
else:  #: for bloxberg
    GAS_PRICE = 0.004  # was 1.21 Gwei

EXIT_AFTER = 1000  # seconds


class Base:
    """Import base functions."""

    from broker.eblocbroker_scripts.authenticate_orc_id import authenticate_orc_id  # type: ignore
    from broker.eblocbroker_scripts.data import get_data_info  # type: ignore
    from broker.eblocbroker_scripts.get_job_info import (  # type: ignore
        analyze_data,
        fetch_log_data_storage_request,
        get_job_code_hashes,
        get_job_info,
        get_job_info_print,
        get_job_state,
        get_job_transfer,
        set_job_received_bn,
        update_job_cores,
    )
    from broker.eblocbroker_scripts.get_provider_info import get_provider_info  # type: ignore
    from broker.eblocbroker_scripts.get_requester_info import get_requester_info  # type: ignore
    from broker.eblocbroker_scripts.log_job import run_log_cancel_refund, run_log_job  # type: ignore
    from broker.eblocbroker_scripts.process_payment import process_payment  # type: ignore
    from broker.eblocbroker_scripts.refund import refund  # type: ignore
    from broker.eblocbroker_scripts.register_provider import _register_provider  # type: ignore
    from broker.eblocbroker_scripts.register_requester import register_requester  # type: ignore
    from broker.eblocbroker_scripts.submit_job import (  # type: ignore
        check_before_submit,
        is_provider_valid,
        is_requester_valid,
        submit_job,
    )
    from broker.eblocbroker_scripts.transfer import transfer_tokens  # type: ignore
    from broker.eblocbroker_scripts.update_provider_info import (  # type: ignore
        is_provider_info_match,
        update_provider_info,
    )
    from broker.eblocbroker_scripts.update_provider_prices import update_provider_prices  # type: ignore


class Contract(Base):
    """Object to access ebloc-broker smart-contract functions."""

    def __init__(self, is_brownie=False) -> None:
        """Create a new Contrect."""
        self.EBB_SCRIPTS = env.EBB_SCRIPTS
        mc = MongoClient()
        self.mongo_broker = MongoBroker(mc, mc["ebloc_broker"]["cache"])
        self.ops = {}
        self.max_retries = 3
        self.required_confs = 1
        self._from = ""
        #: tx cost exceeds current gas limit. Limit: 9990226, got:
        #: ('insufficient funds for gas * price + value',)
        if cfg.NETWORK_ID == "sepolia":
            self.gas = 1000000
        else:  #: brownie
            self.gas = 9900000

        self.gas_price = GAS_PRICE
        # self.gas_params = {"gas_price": self.gas_strategy, "gas": self.gas}
        self._setup(is_brownie)
        self.invalid = {"logs", "logsBloom"}
        with suppress(Exception):
            self.deployed_block_number = self.get_deployed_block_number()

    def _setup(self, is_brownie=False):
        if is_brownie:
            from brownie import web3

            self.w3 = web3
        else:
            try:
                from broker.imports import connect

                self.eBlocBroker, self.w3, self._eblocbroker = connect()
                self.usdtmy = config.usdtmy
            except Exception as e:
                print_tb(e)

    def brownie_load_account(self, fn="", password="alper"):
        """Load accounts from Brownie for Bloxberg."""
        cfg = Yaml(env.LOG_DIR / ".bloxberg_account.yaml")
        if not fn:
            fn = cfg["config"]["name"]

        if cfg["config"]["passw"]:
            password = cfg["config"]["passw"]

        full_path = expanduser(f"~/.brownie/accounts/{fn}")
        if not full_path:
            raise Exception(f"{full_path} does not exist")

        # accounts.load("alper.json", password="alper")  # DELETE
        return accounts.load(fn, password=password)

    def is_eth_account_locked(self, addr):
        """Check whether the ethereum account is locked."""
        if env.IS_TESTNET:
            try:
                account = self.brownie_load_account()
            except Exception as e:
                error_msg = f"E: PROVIDER_ID({env.PROVIDER_ID}) is locked, unlock it for futher use. \n{e}"
                terminate(error_msg, is_traceback=True)
        else:
            for account in self.w3.geth.personal.list_wallets():
                _address = account["accounts"][0]["address"]
                if _address == addr:
                    if account["status"] == "Locked":
                        error_msg = f"E: PROVIDER_ID({_address}) is locked, unlock it for futher use"
                        terminate(error_msg, is_traceback=False)

    def is_synced(self):
        """Check whether the web3 is synced."""
        return self.w3.eth.syncing

    def timenow(self) -> int:
        return self.w3.eth.get_block(self.get_block_number())["timestamp"]

    def to_gwei(self, value):
        return self.w3.toWei(value, "gwei")

    def _wait_for_transaction_receipt(self, tx_hash, compact=False, is_verbose=False) -> TxReceipt:
        """Wait till the tx is deployed."""
        if isinstance(tx_hash, TransactionReceipt):
            tx_hash = tx_hash.txid

        attempt = 0
        poll_latency = 3
        if is_verbose:
            log(f"==> waiting for the tx={tx_hash} receipt...", end="")

        tx_receipt = None
        while True:
            try:
                tx_receipt = cfg.w3.eth.get_transaction_receipt(tx_hash)
            except TransactionNotFound as e:
                log(f"warning: TransactionNotFound tx={tx_hash} {e}")
                if attempt == 5:
                    raise Exception("TransactionNotFound")
            except Exception as e:
                print_tb(e)
                tx_receipt = None

            if tx_receipt and tx_receipt["blockHash"]:
                break

            if is_verbose:
                log()
                log(f"==> attempt={attempt} | sleeping_for={poll_latency} seconds ", end="")

            attempt += 1
            time.sleep(poll_latency)

        if is_verbose:
            log(ok())

        if compact:
            return without_keys(tx_receipt, self.invalid)
        else:
            return tx_receipt

    def tx_id(self, tx):
        """Return transaction id."""
        if env.IS_TESTNET:
            return tx.txid

        if not tx:
            raise Exception("E: Tx is None")

        return tx.hex()

    def get_deployed_block_number(self) -> int:
        """Return contract's deployed block number."""
        try:
            contract = self._get_contract_yaml()
        except Exception as e:
            print_tb(e)
            return False

        block_number: int = self.w3.eth.get_transaction(contract["eBlocBroker"]["tx_hash"]).blockNumber
        if not block_number:
            raise Exception("Contract is not available on the blockchain, is it synced?")

        return block_number

    def is_transaction_passed(self, tx_hash) -> bool:
        try:
            return bool(self.get_transaction_receipt(tx_hash)["status"])
        except Exception as e:
            print_tb(e)
            raise e

    def is_transaction_valid(self, tx_hash) -> bool:
        pattern = re.compile(r"^0x[a-fA-F0-9]{64}")
        return bool(re.fullmatch(pattern, tx_hash))

    def get_transaction_by_block(self, block_hash, tx_index) -> dict:
        """Return the tx at the index specified by transaction_index from the block specified by block_identifier.

        __ https://web3py.readthedocs.io/en/stable/web3.eth.html#web3.eth.Eth.get_transaction_by_block
        """
        return dict(self.w3.eth.get_transaction_by_block(block_hash, tx_index))

    def get_transaction_receipt(self, tx, compact=False):
        """Get the transaction receipt.

        Returns the transaction receipt specified by transactionHash.
        If the transaction has not yet been mined returns 'None'

        __ web3py.readthedocs.io/en/stable/web3.eth.html#web3.eth.Eth.get_transaction_receipt
        """
        tx_receipt = self.w3.eth.get_transaction_receipt(tx)
        if not compact:
            return dict(tx_receipt)
        else:
            return without_keys(tx_receipt, self.invalid)

    def _is_web3_connected(self):
        try:
            message = "* is_web3_connected=True"
            message_no_color = "* is_web3_connected="
            with Halo(text=message_no_color, spinner="line", placement="right"):
                if not Ebb.is_web3_connected():
                    raise Exception("web3 is not connected")

            log(message)
        except subprocess.CalledProcessError as e:
            log(f"{message} FAILED.\n{e.output.decode('utf-8').strip()}")
            self._is_web3_connected()

    def is_web3_connected(self):
        """Return whether web3 connected or not."""
        return self.w3.isConnected()

    def account_id_to_address(self, address: str, account_id=None):
        """Convert account id into address."""
        if address:
            return self.w3.toChecksumAddress(address)

        if isinstance(account_id, int):
            try:
                account = self.w3.eth.accounts[account_id]
                return self.w3.toChecksumAddress(account)
            except Exception as e:
                raise Exception("Given index account does not exist, check .eblocpoa/keystore") from e
        else:
            raise Exception(f"Invalid account {address} is provided")

    def _get_balance(self, account, eth_unit="ether"):
        """Return ether balance of the account"""
        if not isinstance(account, (Account, LocalAccount)):
            account = self.w3.toChecksumAddress(account)
        else:
            account = str(account)

        return self.w3.fromWei(self.w3.eth.get_balance(account), eth_unit)

    def transfer(self, amount, from_account, to_account, required_confs=1):
        """Transfer acount's ether balance."""
        tx = from_account.transfer(to_account, amount, gas_price=f"{GAS_PRICE} gwei", required_confs=required_confs)
        return self.tx_id(tx)

    def fetch_logs(self):
        pass

    def get_block(self, block_number: int):
        """Return block."""
        return self.w3.eth.get_block(block_number)

    def get_block_number(self):
        """Return block number."""
        return self.w3.eth.block_number

    def is_address(self, addr):
        try:
            return self.w3.isAddress(addr)
        except Exception as e:
            print_tb(e)
            raise Web3NotConnected from e

    def _get_contract_yaml(self):
        try:
            _yaml = Yaml(env.CONTRACT_YAML_FILE, auto_dump=False)
            if env.IS_TESTNET:
                net = cfg.NETWORK_ID
                if "bloxberg" in cfg.NETWORK_ID:
                    net = "bloxberg"

                return _yaml["networks"][net]
            elif env.IS_EBLOCPOA:
                return _yaml["networks"]["eblocpoa"]
            else:
                raise Exception("wrong contract yaml address setup")
        except Exception as e:
            raise e

    def is_contract_exists(self) -> bool:
        try:
            contract = self._get_contract_yaml()
        except Exception as e:
            raise e

        contract_address = self.w3.toChecksumAddress(contract["eBlocBroker"]["address"])
        if self.w3.eth.get_code(contract_address) == "0x" or self.w3.eth.get_code(contract_address) == b"":
            raise Exception("Empty contract")

        log(f"==> [y]contract_address[/y]=[cyan]{contract_address.lower()}", h=False)
        return True

    def print_contract_info(self):
        """Print contract information."""
        print(f"==> address={self.eBlocBroker.contract_address}")
        print(f"==> deployed_block_number={self.get_deployed_block_number()}")

    # ~~~~~~~~~~ #
    # Timeout Tx #
    # ~~~~~~~~~~ #
    @exit_after(EXIT_AFTER)
    def timeout(self, func, contract, *args):
        """Timeout deploy contract's functions.

        brownie usage:
        self.eBlocBroker.submitJob(*args, self.ops)

        geth usage:
        self.eBlocBroker.functions.submitJob(*args).transact(self.ops)

        May give "warning: timeout took too long" in exit_after() functions.

        __ https://blockexplorer.bloxberg.org
        """
        method = None
        try:
            if env.IS_TESTNET:
                fn = self.ops["from"].lower().replace("0x", "") + ".json"
                self.brownie_load_account(fn)
                if contract == "eBlocBroker":
                    method = getattr(self.eBlocBroker, func)
                elif contract == "USDTmy":
                    method = getattr(self.usdtmy, func)
                else:
                    raise Exception()

                return method(*args, self.ops)
            else:
                method = getattr(self.eBlocBroker.functions, func)
                return method(*args).transact(self.ops)
        except AttributeError as e:
            raise Exception(f"Method {method} is not implemented") from e
        # except Exception as e:
        #     breakpoint()  # DEBUG

    def timeout_wrapper(self, method, contract, *args):
        idx = 0
        if method == "processPayment":
            self.max_retries = 20

        first_try_flag = False
        while idx < self.max_retries:
            if cfg.NETWORK_ID == "sepolia":
                self.ops = {
                    "from": self._from,
                    "allow_revert": True,
                    "required_confs": self.required_confs,
                    # "gas_price": f"{self.gas_price} gwei",
                }
            else:
                self.ops = {
                    "from": self._from,
                    "gas": self.gas,
                    "gas_price": f"{self.gas_price} gwei",
                    "allow_revert": True,
                    "required_confs": self.required_confs,
                }

            try:
                if first_try_flag:
                    # __ https://eth-brownie.readthedocs.io/en/stable/core-chain.html#core-chain-history
                    log(f"Attempt={idx} | gas_price={self.gas_price} ...")
                    # log(f"==> Sleeping for 15 seconds | gas_price={self.gas_price} ... ", end="")
                    # try:
                    #     time.sleep(15)
                    # except Exception as e:
                    #     log(f"E: {e}")

                    # log(ok())
                    log(history.filter(sender=self._from))

                return self.timeout(method, contract, *args)
            except ValueError as e:
                first_try_flag = True
                if "MAC mismatch" in str(e):
                    log("Please check your Ethereum account password")
                    print_tb(e)
                    raise QuietExit from e

                if "sepolia" not in env.BLOXBERG_HOST:
                    try:
                        nc(env.BLOXBERG_HOST, 8545)
                    except Exception:
                        log(f"E: Failed to make TCP connecton to {env.BLOXBERG_HOST}")

                if "Sequence has incorrect length" in str(e):
                    print_tb(e)
                    raise QuietExit from e

                if "There is another transaction with same nonce in the queue" in str(e):
                    log(f"warning: Tx: {e}", is_code=True)
                else:
                    log(f"E: Tx: {e}")

                if ("Try increasing the gas price" in str(e)) or (
                    "Transaction with the same hash was already imported." in str(e)
                ):
                    if self.gas_price < 1:
                        self.gas_price *= 1.13
                        log(f"==> new_gas_price={self.gas_price} | idx={idx}")
                    else:
                        idx += 1

                    continue
                else:
                    self.gas_price = GAS_PRICE

                if "Execution reverted" in str(e) or "Insufficient funds" in str(e):
                    print_tb(e)
                    raise QuietExit from e

                if "Request has been rejected because of queue limit" in str(e):
                    if self.ops["allow_revert"]:
                        self.ops["allow_revert"] = False
                        try:
                            return self.timeout(method, contract, *args)
                        except Exception as e1:
                            log(str(e1), is_wrap=True)
                            raise QuietExit from e1

                    raise QuietExit from e

                if "Transaction cost exceeds current gas limit" in str(e):
                    self.gas -= 10000
            except KeyboardInterrupt:
                log(f"warning: Timeout Awaiting Transaction in the mempool | gas_price={self.gas_price}")
                if self.gas_price < 1:
                    self.gas_price *= 1.13
                    log(f"==> new_gas_price={self.gas_price}")
                else:
                    idx += 1

                continue
            except Exception as e:
                log(f"Exception: {e}")
                # brownie.exceptions.TransactionError: Tx dropped without known replacement
                if "Tx dropped without known replacement" in str(e):
                    if self.gas_price < 2:
                        self.gas_price *= 1.13
                        log(f"==> new_gas_price={self.gas_price}")
                    else:
                        idx += 1

                    log("Sleep 15 seconds, will try again...")
                    time.sleep(15)
                    continue

                raise e

            idx += 1

    # ~~~~~~~~~~~~ #
    # Transactions #
    # ~~~~~~~~~~~~ #
    def _submit_job(self, required_confs, requester, job_price, *args) -> "TransactionReceipt":
        try:
            # self.approve(env.CONTRACT_ADDRESS, requester, job_price)
            log()
            self.gas_price = GAS_PRICE
            self._from = requester
            self.required_confs = 1
            self.timeout_wrapper("approve", "USDTmy", env.CONTRACT_ADDRESS, job_price)
        except Exception as e:
            raise Exception(f"Approve transaction is failed, {e}")

        time.sleep(2)
        self.gas_price = GAS_PRICE
        method_name = "submitJob"
        idx = 0
        while idx < self.max_retries:
            if cfg.NETWORK_ID == "sepolia":
                self.ops = {
                    "gas": self.gas,
                    # "gas_price": f"{self.gas_price} gwei",  # brownie sets it dynamically
                    "from": requester,
                    "allow_revert": True,
                    "required_confs": required_confs,
                }
            else:
                self.ops = {
                    "gas": self.gas,
                    "gas_price": f"{self.gas_price} gwei",
                    "from": requester,
                    "allow_revert": True,
                    "required_confs": required_confs,
                }

            try:
                return self.timeout(method_name, "eBlocBroker", *args)
            except ValueError as e:
                log(f"E: {WHERE()} {e}")
                if "Insufficient funds" in str(e) or "Execution reverted" in str(e):
                    raise e

                if "Transaction cost exceeds current gas limit" in str(e):
                    self.gas -= 10000
                    continue

                if "Try increasing the gas price" in str(e):
                    if self.gas_price < 2:
                        self.gas_price *= 1.13
                        log(f"==> new_gas_price={self.gas_price}")
                    else:  # if idx += 1 done it remains in an endless loop
                        idx += 1

                    continue
            except KeyboardInterrupt as e:  # acts as Exception
                if str(e):
                    log(f"E: {WHERE()} {e}", is_wrap=True)

                if "Awaiting Transaction in the mempool" in str(e):
                    log("warning: Timeout Awaiting Transaction in the mempool")
                    if self.gas_price < 2:
                        self.gas_price *= 1.13
                        log(f"==> new_gas_price={self.gas_price}")
                    else:
                        idx += 1

                    continue

            time.sleep(2)
            idx += 1
        raise Exception("No valid Tx receipt for 'submitJob' is generated")

    def approve(self, _from, to, amount) -> "TransactionReceipt":
        self.gas_price = GAS_PRICE
        self._from = self.w3.toChecksumAddress(to)
        self.required_confs = 1
        return self.timeout_wrapper("approve", "USDTmy", _from, amount)

    def deposit_storage(self, data_owner, code_hash, _from) -> "TransactionReceipt":
        self.gas_price = GAS_PRICE
        self._from = self.w3.toChecksumAddress(_from)
        self.required_confs = 1
        return self.timeout_wrapper("depositStorage", "eBlocBroker", data_owner, code_hash)

    def _register_requester(self, _from, *args) -> "TransactionReceipt":
        self.gas_price = GAS_PRICE
        self._from = _from
        self.required_confs = 1
        return self.timeout_wrapper("registerRequester", "eBlocBroker", *args)

    def _refund(self, _from, *args) -> "TransactionReceipt":
        self.gas_price = GAS_PRICE
        self._from = _from
        self.required_confs = 1
        # TODO: raise RPCRequestError causes driver to crash does not continue, why?
        return self.timeout_wrapper("refund", "eBlocBroker", *args)

    def _transfer_ownership(self, _from, new_owner) -> "TransactionReceipt":
        self.gas_price = GAS_PRICE
        self._from = _from
        self.required_confs = 1
        return self.timeout_wrapper("transferOwnership", "eBlocBroker", new_owner)

    def transfer_from(self, _from, to, amount):
        fn = to.lower().replace("0x", "") + ".json"
        self.brownie_load_account(fn)
        self.usdtmy.transferFrom(_from, to, amount, {"from": to})

    def _transfer(self, _from, *args) -> "TransactionReceipt":
        self.gas_price = GAS_PRICE
        self._from = _from
        self.required_confs = 1
        return self.timeout_wrapper("transfer", "USDTmy", *args)

    def _authenticate_orc_id(self, _from, *args) -> "TransactionReceipt":
        self.gas_price = GAS_PRICE
        self._from = _from
        self.required_confs = 1
        return self.timeout_wrapper("authenticateOrcID", "eBlocBroker", *args)

    def _update_provider_prices(self, *args) -> "TransactionReceipt":
        self.gas_price = GAS_PRICE
        self._from = env.PROVIDER_ID
        self.required_confs = 1
        return self.timeout_wrapper("updateProviderPrices", "eBlocBroker", *args)

    def _update_provider_info(self, *args) -> "TransactionReceipt":
        self.gas_price = GAS_PRICE
        self._from = env.PROVIDER_ID
        self.required_confs = 1
        return self.timeout_wrapper("updateProviderInfo", "eBlocBroker", *args)

    def register_provider(self, *args) -> "TransactionReceipt":
        """Register provider."""
        self.gas_price = GAS_PRICE
        self._from = env.PROVIDER_ID
        self.required_confs = 1
        return self.timeout_wrapper("registerProvider", "eBlocBroker", *args)

    def register_data(self, *args) -> "TransactionReceipt":
        """Register the dataset hash."""
        self.gas_price = GAS_PRICE
        self._from = env.PROVIDER_ID
        self.required_confs = 1
        return self.timeout_wrapper("registerData", "eBlocBroker", *args)

    def update_data_price(self, *args) -> "TransactionReceipt":
        """Register the dataset hash."""
        self.gas_price = GAS_PRICE
        self._from = env.PROVIDER_ID
        self.required_confs = 1
        return self.timeout_wrapper("updataDataPrice", "eBlocBroker", *args)

    def set_data_verified(self, *args) -> "TransactionReceipt":
        """Set data hashes as verified."""
        self.gas_price = GAS_PRICE
        self._from = env.PROVIDER_ID
        self.required_confs = 0
        return self.timeout_wrapper("setDataVerified", "eBlocBroker", *args)

    def set_job_state_running(self, key, index, job_id, start_timestamp) -> "TransactionReceipt":
        """Set the job state as running."""
        _from = self.w3.toChecksumAddress(env.PROVIDER_ID)
        self._from = _from
        self.required_confs = 1  # "1" safer to wait for confirmation
        return self.timeout_wrapper(
            "setJobStateRunning", "eBlocBroker", key, int(index), int(job_id), int(start_timestamp)
        )

    def _process_payment(self, *args) -> "TransactionReceipt":
        self.gas_price = GAS_PRICE
        self._from = env.PROVIDER_ID
        self.required_confs = 1  # "1" safer to wait for confirmation
        return self.timeout_wrapper("processPayment", "eBlocBroker", *args)

    def remove_registered_data(self, *args) -> "TransactionReceipt":
        """Remove registered data."""
        self.gas_price = GAS_PRICE
        self._from = env.PROVIDER_ID
        self.required_confs = 0
        return self.timeout_wrapper("removeRegisteredData", "eBlocBroker", *args)

    # ~~~~~~~ #
    # GETTERS #
    # ~~~~~~~ #
    def get_registered_data_bn(self, *args):
        if self.eBlocBroker is not None:
            if env.IS_TESTNET:
                return self.eBlocBroker.getRegisteredDataBlockNumbers(*args)
            else:
                return self.eBlocBroker.functions.getRegisteredDataBlockNumbers(*args).call()
        else:
            raise Exception("Contract object's eBlocBroker variable is None")

    def get_registered_data_price(self, *args):
        if self.eBlocBroker is not None:
            if env.IS_TESTNET:
                return self.eBlocBroker.getRegisteredDataPrice(*args)
            else:
                return self.eBlocBroker.functions.getRegisteredDataPrice(*args).call()
        else:
            raise Exception("Contract object's eBlocBroker variable is None")

    def get_provider_prices_blocks(self, account):
        """Return block numbers where provider info is changed.

        First one is the most recent and latest one is the latest block number where
        provider info is changed.
        Ex: (12878247, 12950247, 12952047, 12988647)
        """
        if self.eBlocBroker is not None:
            if env.IS_TESTNET:
                return self.eBlocBroker.getUpdatedProviderPricesBlocks(account)
            else:
                return self.eBlocBroker.functions.getUpdatedProviderPricesBlocks(account).call()
        else:
            raise Exception("Contract object's eBlocBroker variable is None")

    def is_owner(self, address) -> bool:
        """Check if the given address is the owner of the contract."""
        return address.lower() == self.get_owner().lower()

    def _get_provider_fees_for_job(self, *args):
        if self.eBlocBroker is not None:
            if env.IS_TESTNET:
                return self.eBlocBroker.getProviderPrices(*args)  # NOQA
            else:
                return self.eBlocBroker.functions.getProviderPrices(*args).call()  # noqa
        else:
            raise Exception("Contract object's eBlocBroker variable is None")

    def _get_job_info(self, *args):
        if self.eBlocBroker is not None:
            if env.IS_TESTNET:
                return self.eBlocBroker.getJobInfo(*args)
            else:
                return self.eBlocBroker.functions.getJobInfo(*args).call()
        else:
            raise Exception("Contract object's eBlocBroker variable is None")

    def get_user_orcid(self, user):
        if self.eBlocBroker is not None:
            if env.IS_TESTNET:
                return self.eBlocBroker.getOrcID(user)
            else:
                return self.eBlocBroker.functions.getOrcID(user).call()
        else:
            raise Exception("Contract object's eBlocBroker variable is None")

    def _get_requester_info(self, requester):
        if self.eBlocBroker is not None:
            if env.IS_TESTNET:
                committed_block_num = self.eBlocBroker.getRequesterCommittmedBlock(requester)
            else:
                committed_block_num = self.eBlocBroker.functions.getRequesterCommittmedBlock(requester).call()

            return committed_block_num, self.get_user_orcid(requester)
        else:
            raise Exception("Contract object's eBlocBroker variable is None")

    def allowance(self, _from, to):
        """Return the owner of ebloc-broker."""
        if self.usdtmy is not None:
            if env.IS_TESTNET:
                return self.usdtmy.allowance(_from, to)
            else:
                return self.eBlocBroker.functions.allowance().call()
        else:
            raise Exception("Contract object's eBlocBroker variable is None")

    def get_owner(self):
        """Return the owner of ebloc-broker."""
        if self.eBlocBroker is not None:
            if env.IS_TESTNET:
                return self.eBlocBroker.getOwner()
            else:
                return self.eBlocBroker.functions.getOwner().call()
        else:
            raise Exception("Contract object's eBlocBroker variable is None")

    def get_job_size(self, provider, key):
        """Return size of the job."""
        if self.eBlocBroker is not None:
            if env.IS_TESTNET:
                return self.eBlocBroker.getJobSize(provider, key)
            else:
                return self.eBlocBroker.call().getJobSize(provider, key)
        else:
            raise Exception("Contract object's eBlocBroker variable is None")

    def is_orcid_verified(self, address):
        if self.eBlocBroker is not None:
            if env.IS_TESTNET:
                return self.eBlocBroker.isOrcIDVerified(address)
            else:
                return self.eBlocBroker.functions.isOrcIDVerified(address).call()
        else:
            raise Exception("Contract object's eBlocBroker variable is None")

    def does_requester_exist(self, address):
        """Check whether the given Ethereum address of the requester address is registered."""
        if not isinstance(address, (Account, LocalAccount)):
            address = self.w3.toChecksumAddress(address)

        if self.eBlocBroker is not None:
            if env.IS_TESTNET:
                return self.eBlocBroker.doesRequesterExist(address)
            else:
                return self.eBlocBroker.functions.doesRequesterExist(address).call()
        else:
            raise Exception("Contract object's eBlocBroker variable is None")

    def does_provider_exist(self, address) -> bool:
        """Check whether the given provider is registered."""
        if not isinstance(address, (Account, LocalAccount)):
            address = self.w3.toChecksumAddress(address)

        if self.eBlocBroker is not None:
            if env.IS_TESTNET:
                return self.eBlocBroker.doesProviderExist(address)
            else:
                return self.eBlocBroker.functions.doesProviderExist(address).call()
        else:
            raise Exception("Contract object's eBlocBroker variable is None")

    def get_provider_receipt_node(self, provideress, index):
        """Return provider's receipt node based on given index."""
        if self.eBlocBroker is not None:
            if env.IS_TESTNET:
                return self.eBlocBroker.getProviderReceiptNode(provideress, index)
            else:
                return self.eBlocBroker.functions.getProviderReceiptNode(provideress, index).call()
        else:
            raise Exception("Contract object's eBlocBroker variable is None")

    def get_provider_receipt_size(self, address):
        """Return provider receipt size."""
        if not isinstance(address, (Account, LocalAccount)):
            address = self.w3.toChecksumAddress(address)

        if self.eBlocBroker is not None:
            if env.IS_TESTNET:
                return self.eBlocBroker.getProviderReceiptSize(address)
            else:
                return self.eBlocBroker.functions.getProviderReceiptSize(address).call()
        else:
            raise Exception("Contract object's eBlocBroker variable is None")

    def _is_orc_id_verified(self, address):
        if self.eBlocBroker is not None:
            if env.IS_TESTNET:
                return self.eBlocBroker.isOrcIDVerified(address)
            else:
                return self.eBlocBroker.functions.isOrcIDVerified(address).call()
        else:
            raise Exception("Contract object's eBlocBroker variable is None")

    def _get_provider_info(self, provider, prices_set_block_number=0):
        """Fetch price of the provider within the commitment duration."""
        if self.eBlocBroker is not None:
            if env.IS_TESTNET:
                block_read_from, provider_price_info = self.eBlocBroker.getProviderInfo(
                    provider, prices_set_block_number
                )
            else:
                block_read_from, provider_price_info = self.eBlocBroker.functions.getProviderInfo(
                    provider, prices_set_block_number
                ).call()

            return block_read_from, provider_price_info
        else:
            raise Exception("Contract object's eBlocBroker variable is None")

    def gwei_balance(self, account):
        """Return account balance in Gwei."""
        return self.w3.fromWei(self.w3.eth.get_balance(account), "gwei")

    def _pre_check(self, requester):
        balance = Ebb.get_balance(requester)
        if balance == 0:
            raise QuietExit("Requester's balance is zero")

        if len(Ebb.get_providers()) == 0:
            raise QuietExit("There is no provider registered to submit jobs.")

    def get_balance(self, account):
        if not isinstance(account, (Account, LocalAccount)):
            account = self.w3.toChecksumAddress(account)

        if self.usdtmy is not None:
            if env.IS_TESTNET:
                return self.usdtmy.balanceOf(account)
            else:
                return self.usdtmy.functions.balanceOf(account).call()
        else:
            raise Exception("Contract object's eBlocBroker variable is None")

    def get_providers(self):
        """Return the providers list."""
        if self.eBlocBroker is not None:
            if env.IS_TESTNET:
                return self.eBlocBroker.getProviders()
            else:
                return self.eBlocBroker.functions.getProviders().call()
        else:
            raise Exception("Contract object's eBlocBroker variable is None")

    def _get_provider_set_block_numbers(self, provider):
        if self.eBlocBroker is not None:
            if env.IS_TESTNET:
                return self.eBlocBroker.getProviderSetBlockNumbers(provider)[-1]
            else:
                return self.eBlocBroker.functions.getProviderSetBlockNumbers(provider).call()[-1]
        else:
            raise Exception("Contract object's eBlocBroker variable is None")

    def get_job_storage_duration(self, provider, requester, code_hash):
        """Return job's storage duration."""
        if not isinstance(provider, (Account, LocalAccount)):
            provider = self.w3.toChecksumAddress(provider)

        if isinstance(code_hash, str):
            with suppress(Exception):
                code_hash = ipfs_to_bytes32(code_hash)

        if self.eBlocBroker is not None:
            if env.IS_TESTNET:
                return self.eBlocBroker.getStorageInfo(provider, requester, code_hash)
            else:
                return self.eBlocBroker.functions.getStorageInfo(provider, requester, code_hash).call()
        else:
            raise Exception("Contract object's eBlocBroker variable is None")

    def get_storage_info(self, code_hash, provider=env.PROVIDER_ID, data_owner=cfg.ZERO_ADDRESS):
        """Return the received storage deposit for the corresponding source code hash."""
        if isinstance(code_hash, str):
            if len(code_hash) == 32:
                code_hash = code_hash.encode("utf-8")
            else:
                with suppress(Exception):
                    code_hash = ipfs_to_bytes32(code_hash)

        if self.eBlocBroker is not None:
            if env.IS_TESTNET:
                return self.eBlocBroker.getStorageInfo(provider, data_owner, code_hash)
            else:
                return self.eBlocBroker.functions.getStorageInfo(provider, data_owner, code_hash).call()
        else:
            raise Exception("Contract object's eBlocBroker variable is None")

    def search_best_provider(self, job, requester, is_verbose=False):
        selected_provider = ""
        selected_price = 0
        price_to_select = sys.maxsize
        for provider in Ebb.get_providers():
            _price, *_ = job.cost(provider, requester, is_verbose)
            log(f" * provider={provider} | price={_price}")
            if _price < price_to_select:
                selected_provider = provider
                selected_price = _price

        return selected_provider, selected_price


class EBB:
    def __init__(self):
        self.eblocbroker: Union[Contract, None] = None

    def _set(self):
        if not self.eblocbroker:
            self.eblocbroker = Contract()

    def set(self):
        self._set()

    def __getattr__(self, name) -> Contract:
        """Return eblocbroker object."""
        self._set()
        return getattr(self.eblocbroker, name)


Ebb = EBB()
