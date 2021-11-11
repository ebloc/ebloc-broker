#!/usr/bin/env python3

import sys
import time
from contextlib import suppress
from os.path import expanduser
from pathlib import Path
from typing import Union

from pymongo import MongoClient
from web3.exceptions import TransactionNotFound
from web3.types import TxReceipt

from broker import cfg
from broker._utils._log import ok
from broker._utils.tools import exit_after, log, print_tb, read_json, without_keys
from broker.config import env
from broker.errors import Web3NotConnected
from broker.libs.mongodb import MongoBroker
from broker.utils import ipfs_to_bytes32, terminate
from brownie.network.account import Account, LocalAccount
from brownie.network.gas.strategies import LinearScalingStrategy
from brownie.network.transaction import TransactionReceipt

GAS_PRICE = 1.0
EXIT_AFTER = 120


class Contract:
    """Object to access smart-contract functions."""

    def __init__(self, is_brownie=False) -> None:
        """Create a new Contrect."""
        mc = MongoClient()
        self.mongo_broker = MongoBroker(mc, mc["ebloc_broker"]["cache"])
        # self.gas_limit = "max"  # 300000
        self.ops = {}
        self.max_retries = 10
        self.required_confs = 1
        self._from = ""
        #: Transaction cost exceeds current gas limit. Limit: 9990226, got:
        #  10000000. Try decreasing supplied gas.
        self.gas = 9980000
        self.gas_strategy = LinearScalingStrategy(f"{GAS_PRICE} gwei", "10 gwei", 1.1, time_duration=15)
        self.gas_price = GAS_PRICE
        self.gas_params = {"gas_price": self.gas_strategy, "gas": self.gas}
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

                self.eBlocBroker, self.w3, self._eBlocBroker = connect()
            except Exception as e:
                print_tb(e)
                sys.exit(1)

    ebb = None  # contract object

    # Imported methods
    # ================
    from broker.eblocbroker.authenticate_orc_id import authenticate_orc_id
    from broker.eblocbroker.get_provider_info import get_provider_info
    from broker.eblocbroker.process_payment import process_payment
    from broker.eblocbroker.submit_job import submit_job
    from broker.eblocbroker.submit_job import check_before_submit
    from broker.eblocbroker.submit_job import is_provider_valid
    from broker.eblocbroker.submit_job import is_requester_valid
    from broker.eblocbroker.get_job_info import get_job_info
    from broker.eblocbroker.get_job_info import get_job_info_print
    from broker.eblocbroker.get_job_info import set_job_received_block_number
    from broker.eblocbroker.get_job_info import update_job_cores
    from broker.eblocbroker.get_job_info import analyze_data
    from broker.eblocbroker.get_job_info import get_job_source_code_hashes
    from broker.eblocbroker.get_requester_info import get_requester_info
    from broker.eblocbroker.log_job import run_log_cancel_refund
    from broker.eblocbroker.log_job import run_log_job
    from broker.eblocbroker.register_provider import _register_provider
    from broker.eblocbroker.refund import refund
    from broker.eblocbroker.register_requester import register_requester
    from broker.eblocbroker.update_provider_info import update_provider_info
    from broker.eblocbroker.update_provider_prices import update_provider_prices
    from broker.eblocbroker.transfer_ownership import transfer_ownership
    from broker.eblocbroker.data import get_data_info

    def brownie_load_account(self, fname="alper.json", password="alper"):
        """Load accounts from Brownie for Bloxberg."""
        from brownie import accounts

        home = expanduser("~")
        fname = "UTC--2021-09-22T20-08-52.242348460Z--3e6ffc5ede9ee6d782303b2dc5f13afeee277aea.json"
        full_path = f"{home}/.brownie/accounts/{fname}"
        if not full_path:
            raise Exception(f"{full_path} does not exist")

        accounts.load("alper.json", password="alper")  # DELETE
        return accounts.load(fname, password=password)

    def is_eth_account_locked(self, addr):
        """Check whether is the ethereum account locked."""
        if env.IS_BLOXBERG:
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
        return self.w3.eth.get_block(self.w3.eth.get_block_number())["timestamp"]

    def _wait_for_transaction_receipt(self, tx_hash, compact=False) -> TxReceipt:
        """Wait till the tx is deployed."""
        tx_receipt = None
        attempt = 0
        poll_latency = 3
        log(f"## Waiting for the transaction({tx_hash}) receipt... ", end="")
        while True:
            try:
                tx_receipt = cfg.w3.eth.get_transaction_receipt(tx_hash)
            except TransactionNotFound as e:
                log(f"warning: {e}")
            except Exception as e:
                print_tb(str(e))
                tx_receipt = None

            if tx_receipt and tx_receipt["blockHash"]:
                break

            log()
            log(f"## attempt={attempt} | sleeping_for={poll_latency} seconds ", end="")
            attempt += 1
            time.sleep(poll_latency)

        log(ok())
        if not compact:
            return tx_receipt
        else:
            return without_keys(tx_receipt, self.invalid)

    def tx_id(self, tx):
        """Return transaction id."""
        if env.IS_BLOXBERG:
            return tx.txid

        return tx.hex()

    def get_deployed_block_number(self) -> int:
        """Return contract's deployed block number."""
        try:
            fname = self._get_contract_fname()
            contract = read_json(fname)
        except Exception as e:
            print_tb(e)
            return False

        block_number = self.w3.eth.get_transaction(contract["txHash"]).blockNumber
        if block_number is None:
            raise Exception("E: Contract is not available on the blockchain, is it synced?")

        return self.w3.eth.get_transaction(contract["txHash"]).blockNumber

    def get_transaction_receipt(self, tx, compact=False):
        """Get transactioon receipt.

        Returns the transaction receipt specified by transactionHash.
        If the transaction has not yet been mined returns 'None'

        __ https://web3py.readthedocs.io/en/stable/web3.eth.html#web3.eth.Eth.get_transaction_receipt
        """
        tx_receipt = self.w3.eth.get_transaction_receipt(tx)
        if not compact:
            return tx_receipt
        else:
            return without_keys(tx_receipt, self.invalid)

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
                raise Exception("E: Given index account does not exist, check .eblocpoa/keystore") from e
        else:
            raise Exception(f"E: Invalid account {address} is provided")

    def _get_balance(self, address):
        if not isinstance(address, (Account, LocalAccount)):
            address = self.w3.toChecksumAddress(address)
        else:
            address = str(address)

        balance_wei = self.w3.eth.get_balance(address)
        return self.w3.fromWei(balance_wei, "ether")

    def get_block_number(self):
        """Retrun block number."""
        return self.w3.eth.block_number

    def is_address(self, addr):
        try:
            return self.w3.isAddress(addr)
        except Exception as e:
            print_tb(e)
            raise Web3NotConnected from e

    def _get_contract_fname(self) -> Path:
        if env.IS_BLOXBERG:
            return Path(f"{env.EBLOCPATH}/broker/eblocbroker/contract_bloxberg.json")
        elif env.IS_EBLOCPOA:
            return Path(f"{env.EBLOCPATH}/broker/eblocbroker/contract_eblocpoa.json")

        raise Exception("There is no corresponding contract.json file matched.")

    def is_contract_exists(self) -> bool:
        try:
            contract = read_json(self._get_contract_fname())
        except Exception as e:
            raise e

        contract_address = self.w3.toChecksumAddress(contract["address"])
        if self.w3.eth.get_code(contract_address) == "0x" or self.w3.eth.get_code(contract_address) == b"":
            raise

        log(f"==> contract_address={contract_address}")
        return True

    def print_contract_info(self):
        """Print contract information."""
        print(f"address={self.eBlocBroker.contract_address}")
        print(f"deployed_block_number={self.get_deployed_block_number()}")

    ##############
    # Timeout Tx #
    ##############
    @exit_after(EXIT_AFTER)
    def timeout(self, func, *args):
        """Timeout deploy contract's functions.

        brownie:
        self.eBlocBroker.submitJob(*args, self.ops)

        geth:
        self.eBlocBroker.functions.submitJob(*args).transact(self.ops)
        """
        method = None
        try:
            if env.IS_BLOXBERG:
                self.brownie_load_account()
                method = getattr(self.eBlocBroker, func)
                return method(*args, self.ops)
            else:
                method = getattr(self.eBlocBroker.functions, func)
                return method(*args).transact(self.ops)
        except AttributeError as e:
            raise Exception(f"Method {method} not implemented") from e

    def timeout_wrapper(self, method, *args):
        for _ in range(self.max_retries):
            self.ops = {
                "gas": self.gas,
                "gas_price": f"{self.gas_price} gwei",
                "from": self._from,
                "allow_revert": True,
                "required_confs": self.required_confs,
            }
            try:
                return self.timeout(method, *args)
            except ValueError as e:
                log(f"E: {e}")
                if "Execution reverted" in str(e):
                    raise e

                if "Transaction cost exceeds current gas limit" in str(e):
                    self.gas -= 10000
            except KeyboardInterrupt:
                log("warning: Timeout Awaiting Transaction in the mempool")
                self.gas_price *= 1.13

    ################
    # Transactions #
    ################
    def _submit_job(self, requester, job_price, *args) -> "TransactionReceipt":
        self.gas_price = GAS_PRICE
        for _ in range(self.max_retries):
            self.ops = {
                "gas": self.gas,
                "gas_price": f"{self.gas_price} gwei",
                "from": requester,
                "allow_revert": True,
                "value": self.w3.toWei(job_price, "wei"),
            }
            try:
                return self.timeout("submitJob", *args)
            except ValueError as e:
                log(f"E: {e}")
                if "Execution reverted" in str(e):
                    raise e

                if "Transaction cost exceeds current gas limit" in str(e):
                    self.gas -= 10000
            except KeyboardInterrupt as e:
                if "Awaiting Transaction in the mempool" in str(e):
                    log("warning: Timeout Awaiting Transaction in the mempool")
                    self.gas_price *= 1.13

    def withdraw(self, account) -> "TransactionReceipt":
        """Withdraw payment."""
        self.gas_price = GAS_PRICE
        self._from = self.w3.toChecksumAddress(account)
        self.required_confs = 1
        return self.timeout_wrapper("withdraw", *args)

    def _register_requester(self, _from, *args) -> "TransactionReceipt":
        self.gas_price = GAS_PRICE
        self._from = _from
        self.required_confs = 1
        return self.timeout_wrapper("registerRequester", *args)

    def _refund(self, _from, *args) -> "TransactionReceipt":
        self.gas_price = GAS_PRICE
        self._from = _from
        self.required_confs = 1
        return self.timeout_wrapper("refund", *args)

    def _transfer_ownership(self, _from, new_owner) -> "TransactionReceipt":
        self.gas_price = GAS_PRICE
        self._from = _from
        self.required_confs = 1
        return self.timeout_wrapper("transferOwnership", new_owner)

    def _authenticate_orc_id(self, _from, *args) -> "TransactionReceipt":
        self.gas_price = GAS_PRICE
        self._from = _from
        self.required_confs = 1
        return self.timeout_wrapper("authenticateOrcID", *args)

    def _update_provider_prices(self, *args) -> "TransactionReceipt":
        self.gas_price = GAS_PRICE
        self._from = env.PROVIDER_ID
        self.required_confs = 1
        return self.timeout_wrapper("updateProviderPrices", *args)

    def _update_provider_info(self, *args) -> "TransactionReceipt":
        self.gas_price = GAS_PRICE
        self._from = env.PROVIDER_ID
        self.required_confs = 1
        return self.timeout_wrapper("updateProviderInfo", *args)

    def register_provider(self, *args) -> "TransactionReceipt":
        """Register provider."""
        self.gas_price = GAS_PRICE
        self._from = env.PROVIDER_ID
        self.required_confs = 1
        return self.timeout_wrapper("registerProvider", *args)

    def register_data(self, *args) -> "TransactionReceipt":
        """Register the dataset hash."""
        self.gas_price = GAS_PRICE
        self._from = env.PROVIDER_ID
        self.required_confs = 1
        return self.timeout_wrapper("registerData", *args)

    def set_job_status_running(self, key, index, job_id, start_time) -> "TransactionReceipt":
        """Set the job status as running."""
        _from = self.w3.toChecksumAddress(env.PROVIDER_ID)
        self._from = _from
        self.required_confs = 0
        return self.timeout_wrapper("setJobStatusRunning", key, int(index), int(job_id), int(start_time))

    def _process_payment(self, *args) -> "TransactionReceipt":
        self.gas_price = GAS_PRICE
        self._from = env.PROVIDER_ID
        self.required_confs = 0
        return self.timeout_wrapper("processPayment", *args)

    def remove_registered_data(self, *args) -> "TransactionReceipt":
        """Remove registered data"""
        self.gas_price = GAS_PRICE
        self._from = env.PROVIDER_ID
        self.required_confs = 0
        return self.timeout_wrapper("removeRegisteredData", *args)

    ###########
    # GETTERS #
    ###########
    def get_registred_data_prices(self, *args):
        if env.IS_BLOXBERG:
            return self.eBlocBroker.getRegisteredDataPrice(*args)
        else:
            return self.eBlocBroker.functions.getRegisteredDataPrice(*args).call()

    def get_provider_prices_blocks(self, account):
        """Return block numbers where provider info is changed.

        First one is the most recent and latest one is the latest block number where
        provider info is changed.
        Ex: (12878247, 12950247, 12952047, 12988647)
        """
        if env.IS_BLOXBERG:
            return self.eBlocBroker.getUpdatedProviderPricesBlocks(account)
        else:
            return self.eBlocBroker.functions.getUpdatedProviderPricesBlocks(account).call()

    def is_owner(self, address) -> bool:
        """Check if the given address is the owner of the contract."""
        return address.lower() == self.get_owner().lower()

    def _get_provider_prices_for_job(self, *args):
        if env.IS_BLOXBERG:
            return self.eBlocBroker.getProviderPricesForJob(*args)
        else:
            return self.eBlocBroker.functions.getProviderPricesForJob(*args).call()

    def _get_job_info(self, *args):
        if env.IS_BLOXBERG:
            return self.eBlocBroker.getJobInfo(*args)
        else:
            return self.eBlocBroker.functions.getJobInfo(*args).call()

    def _get_requester_info(self, requester):
        if env.IS_BLOXBERG:
            return self.eBlocBroker.getRequesterInfo(requester)
        else:
            return self.eBlocBroker.functions.getRequesterInfo(requester).call()

    def get_owner(self):
        """Return the owner of ebloc-broker."""
        if env.IS_BLOXBERG:
            return self.eBlocBroker.getOwner()
        else:
            return self.eBlocBroker.functions.getOwner().call()

    def get_job_size(self, provider, key):
        """Return size of the job."""
        if env.IS_BLOXBERG:
            return self.eBlocBroker.getJobSize(provider, key)
        else:
            return self.eBlocBroker.call().getJobSize(provider, key)

    def is_orcid_verified(self, address):
        if env.IS_BLOXBERG:
            return self.eBlocBroker.isOrcIDVerified(address)
        else:
            return self.eBlocBroker.functions.isOrcIDVerified(address).call()

    def does_requester_exist(self, address):
        """Check whether the given Ethereum address of the requester address is registered."""
        if not isinstance(address, (Account, LocalAccount)):
            address = self.w3.toChecksumAddress(address)

        if env.IS_BLOXBERG:
            return self.eBlocBroker.doesRequesterExist(address)
        else:
            return self.eBlocBroker.functions.doesRequesterExist(address).call()

    def does_provider_exist(self, address) -> bool:
        """Check whether the given provider is registered."""
        if not isinstance(address, (Account, LocalAccount)):
            address = self.w3.toChecksumAddress(address)

        if env.IS_BLOXBERG:
            return self.eBlocBroker.doesProviderExist(address)
        else:
            return self.eBlocBroker.functions.doesProviderExist(address).call()

    def get_provider_receipt_node(self, provider_address, index):
        """Return provider's receipt node based on given index."""
        if env.IS_BLOXBERG:
            return self.eBlocBroker.getProviderReceiptNode(provider_address, index)
        else:
            return self.eBlocBroker.functions.getProviderReceiptNode(provider_address, index).call()

    def get_provider_receipt_size(self, address):
        """Return provider receipt size."""
        if not isinstance(address, (Account, LocalAccount)):
            address = self.w3.toChecksumAddress(address)

        if env.IS_BLOXBERG:
            return self.eBlocBroker.getProviderReceiptSize(address)
        else:
            return self.eBlocBroker.functions.getProviderReceiptSize(address).call()

    def _is_orc_id_verified(self, address):
        if env.IS_BLOXBERG:
            return self.eBlocBroker.isOrcIDVerified(address)
        else:
            return self.eBlocBroker.functions.isOrcIDVerified(address).call()

    def _get_provider_info(self, provider, prices_set_block_number=0):
        if env.IS_BLOXBERG:
            block_read_from, provider_price_info = self.eBlocBroker.getProviderInfo(provider, prices_set_block_number)
        else:
            block_read_from, provider_price_info = self.eBlocBroker.functions.getProviderInfo(
                provider, prices_set_block_number
            ).call()

        return block_read_from, provider_price_info

    def eth_balance(self, account):
        """Return account balance."""
        return self.w3.eth.get_balance(account)

    def get_balance(self, account):
        if not isinstance(account, (Account, LocalAccount)):
            account = self.w3.toChecksumAddress(account)

        if env.IS_BLOXBERG:
            return self.eBlocBroker.balanceOf(account)
        else:
            return self.eBlocBroker.functions.balanceOf(account).call()

    def get_providers(self):
        """Return the providers list."""
        if env.IS_BLOXBERG:
            return self.eBlocBroker.getProviders()
        else:
            return self.eBlocBroker.functions.getProviders().call()

    def _get_provider_set_block_numbers(self, provider):
        if env.IS_BLOXBERG:
            return self.eBlocBroker.getProviderSetBlockNumbers(provider)[-1]
        else:
            return self.eBlocBroker.functions.getProviderSetBlockNumbers(provider).call()[-1]

    def get_job_storage_time(self, provider_addr, source_code_hash):
        """Return job storage duration time."""
        if not isinstance(provider_addr, (Account, LocalAccount)):
            provider_addr = self.w3.toChecksumAddress(provider_addr)

        if isinstance(source_code_hash, str):
            try:
                source_code_hash = ipfs_to_bytes32(source_code_hash)
            except:
                pass

        if env.IS_BLOXBERG:
            return self.eBlocBroker.getJobStorageTime(provider_addr, source_code_hash)
        else:
            return self.eBlocBroker.functions.getJobStorageTime(provider_addr, source_code_hash).call()

    def get_received_storage_deposit(self, provider, requester, source_code_hash):
        """Return received storage deposit for the corresponding source code hash."""
        ops = {"from": provider}
        if isinstance(source_code_hash, str):
            try:
                source_code_hash = ipfs_to_bytes32(source_code_hash)
            except:
                pass

        if env.IS_BLOXBERG:
            return self.eBlocBroker.getReceivedStorageDeposit(provider, requester, source_code_hash, ops)
        else:
            return self.eBlocBroker.functions.getReceivedStorageDeposit(provider, requester, source_code_hash).call(ops)


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


# eblocbroker: Union["Contract", None] = None
Ebb = EBB()
