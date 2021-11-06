#!/usr/bin/env python3

import sys
import time
from os.path import expanduser
from pathlib import Path
from typing import Union

from pymongo import MongoClient
from web3.exceptions import TransactionNotFound
from web3.types import TxReceipt

from broker import cfg
from broker._utils._log import ok
from broker._utils.tools import exit_after, log, print_tb
from broker.config import env
from broker.errors import Web3NotConnected
from broker.libs.mongodb import MongoBroker
from broker.utils import ipfs_to_bytes32, read_json, terminate
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
        #: Transaction cost exceeds current gas limit. Limit: 9990226, got:
        #  10000000. Try decreasing supplied gas.
        self.gas = 9980000
        self.gas_strategy = LinearScalingStrategy(f"{GAS_PRICE} gwei", "10 gwei", 1.1, time_duration=15)
        self.gas_params = {"gas_price": self.gas_strategy, "gas": self.gas}
        self._setup(is_brownie)

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
    from broker.eblocbroker.get_job_info import update_job_cores
    from broker.eblocbroker.get_job_info import get_job_source_code_hashes
    from broker.eblocbroker.get_requester_info import get_requester_info
    from broker.eblocbroker.log_job import run_log_cancel_refund
    from broker.eblocbroker.log_job import run_log_job
    from broker.eblocbroker.register_provider import register_provider
    from broker.eblocbroker.refund import refund
    from broker.eblocbroker.register_requester import register_requester
    from broker.eblocbroker.update_provider_info import update_provider_info
    from broker.eblocbroker.update_provider_prices import update_provider_prices
    from broker.eblocbroker.transfer_ownership import transfer_ownership

    def brownie_load_account(self, fname="alper.json", password="alper"):
        """Load accounts from Brownie for Bloxberg."""
        from brownie import accounts

        home = expanduser("~")
        full_path = f"{home}/.brownie/accounts/{fname}"
        if not full_path:
            raise Exception(f"{full_path} does not exist")

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

    def _wait_for_transaction_receipt(self, tx_hash) -> TxReceipt:
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
        return tx_receipt

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

        block_number = self.w3.eth.getTransaction(contract["txHash"]).blockNumber
        if block_number is None:
            raise Exception("E: Contract is not available on the blockchain, is it synced?")

        return self.w3.eth.getTransaction(contract["txHash"]).blockNumber

    def get_transaction_receipt(self, tx):
        """Get transactioon receipt.

        Returns the transaction receipt specified by transactionHash.
        If the transaction has not yet been mined returns 'None'

        __ https://web3py.readthedocs.io/en/stable/web3.eth.html#web3.eth.Eth.getTransactionReceipt
        """
        return self.w3.eth.getTransactionReceipt(tx)

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
            except:
                raise Exception("E: Given index account does not exist, check .eblocpoa/keystore")
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
        return self.w3.eth.blockNumber

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
        if self.w3.eth.getCode(contract_address) == "0x" or self.w3.eth.getCode(contract_address) == b"":
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
    def set_job_status_running_timeout(self, key, index, job_id, start_time) -> "TransactionReceipt":
        if env.IS_BLOXBERG:
            self.brownie_load_account()
            return self.eBlocBroker.setJobStatusRunning(key, index, job_id, start_time, self.ops)
        else:
            return self.eBlocBroker.functions.setJobStatusRunning(key, index, job_id, start_time).transact(self.ops)

    @exit_after(EXIT_AFTER)
    def process_payment_timeout(self, *args) -> "TransactionReceipt":
        if env.IS_BLOXBERG:
            self.brownie_load_account()
            return self.eBlocBroker.processPayment(*args, self.ops)
        else:
            return self.eBlocBroker.functions.processPayment(*args).transact(self.ops)

    @exit_after(EXIT_AFTER)
    def withdraw_timeout(self) -> "TransactionReceipt":
        if env.IS_BLOXBERG:
            self.brownie_load_account()
            return self.eBlocBroker.withdraw(self.ops)
        else:
            return self.eBlocBroker.functions.withdraw().transact(self.ops)

    @exit_after(EXIT_AFTER)
    def register_data_timeout(self, *args) -> "TransactionReceipt":
        if env.IS_BLOXBERG:
            self.brownie_load_account()
            return self.eBlocBroker.registerData(*args, self.ops)
        else:
            return self.eBlocBroker.functions.registerData(*args).transact(self.ops)

    @exit_after(EXIT_AFTER)
    def set_register_provider_timeout(self, *args) -> "TransactionReceipt":
        if env.IS_BLOXBERG:
            self.brownie_load_account()
            return self.eBlocBroker.registerProvider(*args, self.ops)
        else:
            return self.eBlocBroker.functions.registerProvider(*args).transact(self.ops)

    @exit_after(EXIT_AFTER)
    def _update_provider_info_timeout(self, *args) -> "TransactionReceipt":
        if env.IS_BLOXBERG:
            self.brownie_load_account()
            return self.eBlocBroker.updateProviderInfo(*args, self.ops)
        else:
            return self.eBlocBroker.functions.updateProviderInfo(*args).transact(self.ops)

    @exit_after(EXIT_AFTER)
    def _update_provider_prices_timeout(self, *args) -> "TransactionReceipt":
        if env.IS_BLOXBERG:
            self.brownie_load_account()
            return self.eBlocBroker.updateProviderPrices(*args, self.ops)
        else:
            return self.eBlocBroker.functions.updateProviderPrices(*args).transact(self.ops)

    @exit_after(EXIT_AFTER)
    def _authenticate_orc_id_timeout(self, *args) -> "TransactionReceipt":
        if env.IS_BLOXBERG:
            self.brownie_load_account()
            return self.eBlocBroker.authenticateOrcID(*args, self.ops)
        else:
            return self.eBlocBroker.functions.authenticateOrcID(*args).transact(self.ops)

    @exit_after(EXIT_AFTER)
    def _transfer_ownership_timeout(self, new_owner) -> "TransactionReceipt":
        if env.IS_BLOXBERG:
            self.brownie_load_account()
            return self.eBlocBroker.transferOwnership(new_owner, self.ops)
        else:
            return self.eBlocBroker.functions.transferOwnership(new_owner).transact(self.ops)

    @exit_after(EXIT_AFTER)
    def _refund_timeout(self, *args) -> "TransactionReceipt":
        if env.IS_BLOXBERG:
            self.brownie_load_account()
            return self.eBlocBroker.refund(*args, self.ops)
        else:
            return self.eBlocBroker.functions.refund(*args).transact(self.ops)

    @exit_after(EXIT_AFTER)
    def _register_requester_timeout(self, *args) -> "TransactionReceipt":
        if env.IS_BLOXBERG:
            self.brownie_load_account()
            return self.eBlocBroker.registerRequester(*args, self.ops)
        else:
            return self.eBlocBroker.functions.registerRequester(*args).transact(self.ops)

    @exit_after(EXIT_AFTER)
    def _submit_job_timeout(self, *args) -> "TransactionReceipt":
        if env.IS_BLOXBERG:
            self.brownie_load_account()
            return self.eBlocBroker.submitJob(*args, self.ops)
        else:
            return self.eBlocBroker.functions.submitJob(*args).transact(self.ops)

    ################
    # Transactions #
    ################
    def _submit_job(self, requester, job_price, *args) -> "TransactionReceipt":
        gas_price = GAS_PRICE
        for _ in range(self.max_retries):
            self.ops = {
                "gas": self.gas,
                "gas_price": f"{gas_price} gwei",
                "from": requester,
                "value": self.w3.toWei(job_price, "wei"),
                "allow_revert": True,
            }
            try:
                return self._submit_job_timeout(*args)
            except ValueError as e:
                log(f"E: {e}")
                if "Execution reverted" in str(e):
                    raise e

                if "Transaction cost exceeds current gas limit" in str(e):
                    self.gas -= 10000
            except KeyboardInterrupt as e:
                if "Awaiting Transaction in the mempool" in str(e):
                    log("warning: Timeout Awaiting Transaction in the mempool")
                    gas_price *= 1.13

    def _register_requester(self, _from, *args) -> "TransactionReceipt":
        gas_price = GAS_PRICE
        for _ in range(self.max_retries):
            self.ops = {"gas": self.gas, "gas_price": f"{gas_price} gwei", "from": _from, "allow_revert": True}
            try:
                return self._register_requester_timeout(*args)
            except ValueError as e:
                log(f"E: {e}")
                if "Execution reverted" in str(e):
                    raise e

                if "Transaction cost exceeds current gas limit" in str(e):
                    self.gas -= 10000
            except KeyboardInterrupt:
                log("warning: Timeout Awaiting Transaction in the mempool")
                gas_price *= 1.13

    def _refund(self, _from, *args) -> "TransactionReceipt":
        gas_price = GAS_PRICE
        for _ in range(self.max_retries):
            self.ops = {"gas": self.gas, "gas_price": f"{gas_price} gwei", "from": _from, "allow_revert": True}
            try:
                return self._refund_timeout(*args)
            except ValueError as e:
                log(f"E: {e}")
                if "Execution reverted" in str(e):
                    raise e

                if "Transaction cost exceeds current gas limit" in str(e):
                    self.gas -= 10000
            except KeyboardInterrupt:
                log("warning: Timeout Awaiting Transaction in the mempool")
                gas_price *= 1.13

    def _transfer_ownership(self, _from, new_owner) -> "TransactionReceipt":
        gas_price = GAS_PRICE
        for _ in range(self.max_retries):
            self.ops = {"gas": self.gas, "gas_price": f"{gas_price} gwei", "from": _from, "allow_revert": True}
            try:
                return self._transfer_ownership_timeout(new_owner)
            except ValueError as e:
                log(f"E: {e}")
                if "Execution reverted" in str(e):
                    raise e

                if "Transaction cost exceeds current gas limit" in str(e):
                    self.gas -= 10000
            except KeyboardInterrupt:
                log("warning: Timeout Awaiting Transaction in the mempool")
                gas_price *= 1.13

    def _authenticate_orc_id(self, _from, *args) -> "TransactionReceipt":
        gas_price = GAS_PRICE
        for _ in range(self.max_retries):
            self.ops = {"gas": self.gas, "gas_price": f"{gas_price} gwei", "from": _from, "allow_revert": True}
            try:
                tx = self._authenticate_orc_id_timeout(*args)
                return tx
            except ValueError as e:
                if tx:
                    breakpoint()  # DEBUG

                log(f"E: {e}")
                if "Execution reverted" in str(e):
                    raise e

                if "Transaction cost exceeds current gas limit" in str(e):
                    self.gas -= 10000
            except KeyboardInterrupt:
                log("warning: Timeout Awaiting Transaction in the mempool")
                gas_price *= 1.13

    def _update_provider_prices(self, *args) -> "TransactionReceipt":
        gas_price = GAS_PRICE
        for _ in range(self.max_retries):
            self.ops = {
                "gas": self.gas,
                "gas_price": f"{gas_price} gwei",
                "from": env.PROVIDER_ID,
                "allow_revert": True,
            }
            try:
                return self._update_provider_prices_timeout(*args)
            except ValueError as e:
                log(f"E: {e}")
                if "Execution reverted" in str(e):
                    raise e

                if "Transaction cost exceeds current gas limit" in str(e):
                    self.gas -= 10000
            except KeyboardInterrupt:
                log("warning: Timeout Awaiting Transaction in the mempool")
                gas_price *= 1.13

    def _update_provider_info(self, *args) -> "TransactionReceipt":
        gas_price = GAS_PRICE
        for _ in range(self.max_retries):
            self.ops = {
                "gas": self.gas,
                "gas_price": f"{gas_price} gwei",
                "from": env.PROVIDER_ID,
                "allow_revert": True,
            }
            try:
                return self._update_provider_info_timeout(*args)
            except ValueError as e:
                log(f"E: {e}")
                if "Execution reverted" in str(e):
                    raise e

                if "Transaction cost exceeds current gas limit" in str(e):
                    self.gas -= 10000
            except KeyboardInterrupt:
                log("warning: Timeout Awaiting Transaction in the mempool")
                gas_price *= 1.13

    def set_register_provider(self, *args) -> "TransactionReceipt":
        """Register provider."""
        gas_price = GAS_PRICE
        for _ in range(self.max_retries):
            self.ops = {
                "gas": self.gas,
                "gas_price": f"{gas_price} gwei",
                "from": env.PROVIDER_ID,
                "allow_revert": True,
            }
            try:
                return self.set_register_provider_timeout(*args)
            except ValueError as e:
                log(f"E: {e}")
                if "Execution reverted" in str(e):
                    raise e

                if "Transaction cost exceeds current gas limit" in str(e):
                    self.gas -= 10000
            except KeyboardInterrupt:
                log("warning: Timeout Awaiting Transaction in the mempool")
                gas_price *= 1.13

    def register_data(self, *args) -> "TransactionReceipt":
        """Register the dataset hash."""
        gas_price = GAS_PRICE
        for _ in range(self.max_retries):
            self.ops = {
                "gas": self.gas,
                "gas_price": f"{gas_price} gwei",
                "from": env.PROVIDER_ID,
                "allow_revert": True,
            }
            try:
                return self.register_data_timeout(*args)
            except ValueError as e:
                log(f"E: {e}")
                if "Execution reverted" in str(e):
                    raise e

                if "Transaction cost exceeds current gas limit" in str(e):
                    self.gas -= 10000
            except KeyboardInterrupt:
                log("warning: Timeout Awaiting Transaction in the mempool")
                gas_price *= 1.13

    def set_job_status_running(self, key, index, job_id, start_time) -> "TransactionReceipt":
        """Set the job status as running."""
        _from = self.w3.toChecksumAddress(env.PROVIDER_ID)
        gas_price = GAS_PRICE
        for _ in range(self.max_retries):
            self.ops = {
                "gas": self.gas,
                "gas_price": f"{gas_price} gwei",
                "allow_revert": True,
                "required_confs": 0,
                "from": _from,
            }
            try:
                return self.set_job_status_running_timeout(key, int(index), int(job_id), int(start_time))
            except ValueError as e:
                log(f"E: {e}")
                if "Execution reverted" in str(e):
                    raise e

                if "Transaction cost exceeds current gas limit" in str(e):
                    self.gas -= 10000
            except KeyboardInterrupt:
                log("warning: Timeout Awaiting Transaction in the mempool")
                gas_price *= 1.13

    def _process_payment(self, *args) -> "TransactionReceipt":
        gas_price = GAS_PRICE
        for _ in range(self.max_retries):
            self.ops = {
                "gas": self.gas,
                "gas_price": f"{gas_price} gwei",
                "from": env.PROVIDER_ID,
                "allow_revert": True,
                "required_confs": 0,
            }
            try:
                return self.process_payment_timeout(*args)
            except ValueError as e:
                log(f"E: {e}")
                if "Execution reverted" in str(e):
                    raise e

                if "Transaction cost exceeds current gas limit" in str(e):
                    self.gas -= 10000
            except KeyboardInterrupt:
                log("warning: Timeout Awaiting Transaction in the mempool")
                gas_price *= 1.13

    def withdraw(self, account) -> "TransactionReceipt":
        """Withdraw payment."""
        gas_price = GAS_PRICE
        for _ in range(self.max_retries):
            self.ops = {
                "gas": self.gas,
                "gas_price": f"{gas_price} gwei",
                "from": self.w3.toChecksumAddress(account),
                "allow_revert": True,
            }
            try:
                return self.withdraw_timeout()
            except ValueError as e:
                log(f"E: {e}")
                if "Execution reverted" in str(e):
                    raise e

                if "Transaction cost exceeds current gas limit" in str(e):
                    self.gas -= 10000
            except KeyboardInterrupt:
                log("warning: Timeout Awaiting Transaction in the mempool")
                gas_price *= 1.13

    ###########
    # GETTERS #
    ###########
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

    def _get_provider_info(self, provider, index=0):
        if env.IS_BLOXBERG:
            block_read_from, provider_price_info = self.eBlocBroker.getProviderInfo(provider, index)
        else:
            block_read_from, provider_price_info = self.eBlocBroker.functions.getProviderInfo(provider, index).call()

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

    def get_job_storage_time(self, provider_addr, source_code_hash, _from):
        """Return job storage duration time."""
        if not isinstance(provider_addr, (Account, LocalAccount)):
            provider_addr = self.w3.toChecksumAddress(provider_addr)

        ops = {"from": _from}
        if isinstance(source_code_hash, str):
            try:
                source_code_hash = ipfs_to_bytes32(source_code_hash)
            except:
                pass

        if env.IS_BLOXBERG:
            return self.eBlocBroker.getJobStorageTime(provider_addr, source_code_hash, ops)  # FIXME
        else:
            return self.eBlocBroker.functions.getJobStorageTime(provider_addr, source_code_hash).call(ops)

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

    def timenow(self) -> int:
        return self.w3.eth.get_block(self.w3.eth.get_block_number())["timestamp"]


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
