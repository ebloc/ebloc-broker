#!/usr/bin/env python3

import logging
import sys

from pymongo import MongoClient

from broker._utils.tools import _colorize_traceback, log
from broker.config import env
from broker.libs.mongodb import MongoBroker
from broker.utils import ipfs_to_bytes32, read_json, terminate
from brownie.network.account import Account


class Web3NotConnected(Exception):  # noqa
    pass


class Contract:
    """Object to access smart-contract functions."""

    def __init__(self, is_brownie=False) -> None:
        """Create a new Contrect."""
        mc = MongoClient()
        self.mongo_broker = MongoBroker(mc, mc["ebloc_broker"]["cache"])
        self.gas = 4500000
        self.gas_limit = 300000
        if is_brownie:
            from brownie import web3

            self.w3 = web3
        else:
            try:
                from broker.imports import connect

                self.eBlocBroker, self.w3, self._eBlocBroker = connect()
            except Exception as e:
                _colorize_traceback(e)
                sys.exit(1)

    ebb = None  # contract object

    # Imported methods
    # ================
    from broker.eblocbroker.authenticate_orc_id import authenticate_orc_id
    from broker.eblocbroker.get_provider_info import get_provider_info
    from broker.eblocbroker.process_payment import process_payment
    from broker.eblocbroker.submit_job import submit_job, check_before_submit, is_provider_valid, is_requester_valid
    from broker.eblocbroker.get_job_info import get_job_info, update_job_cores, get_job_source_code_hashes
    from broker.eblocbroker.get_requester_info import get_requester_info
    from broker.eblocbroker.log_job import run_log_cancel_refund, run_log_job
    from broker.eblocbroker.register_provider import register_provider
    from broker.eblocbroker.refund import refund
    from broker.eblocbroker.register_requester import register_requester
    from broker.eblocbroker.update_provider_info import update_provider_info
    from broker.eblocbroker.update_provider_prices import update_provider_prices
    from broker.eblocbroker.transfer_ownership import transfer_ownership

    def brownie_load_accounts(self, fname="alper.json", password="alper"):
        """Load accounts from Brownie for Bloxberg."""
        from brownie import accounts

        return accounts.load(fname, password=password)

    def is_eth_account_locked(self, addr):
        """Check whether is the ethereum account locked."""
        pass
        if env.IS_BLOXBERG:
            try:
                account = self.brownie_load_accounts()
            except:
                terminate(f"E: PROVIDER_ID({account}) is locked, unlock it for futher use", is_traceback=False)
        else:
            for account in self.w3.geth.personal.list_wallets():
                _address = account["accounts"][0]["address"]
                if _address == addr:
                    if account["status"] == "Locked":
                        terminate(f"E: PROVIDER_ID({_address}) is locked, unlock it for futher use", is_traceback=False)

    def is_synced(self):
        """Check whether the web3 is synced."""
        return self.w3.eth.syncing

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
            _colorize_traceback(e)
            return False

        block_number = self.w3.eth.getTransaction(contract["txHash"]).blockNumber
        if block_number is None:
            raise Exception("E: Contract is not available on the blockchain, is it synced?")

        return self.w3.eth.getTransaction(contract["txHash"]).blockNumber

    def get_transaction_receipt(self, tx):
        """Get transactioon receipt.

        Returns the transaction receipt specified by transactionHash.
        If the transaction has not yet been mined returns 'None'

        https://web3py.readthedocs.io/en/stable/web3.eth.html#web3.eth.Eth.getTransactionReceipt
        """
        return self.w3.eth.getTransactionReceipt(tx)

    def is_web3_connected(self):
        return self.w3.isConnected()

    def account_id_to_address(self, address, account_id=None):
        """Convert account id into address."""
        if address:
            return self.w3.toChecksumAddress(address)

        if isinstance(account_id, int):
            try:
                account = self.w3.eth.accounts[account_id]
                return self.w3.toChecksumAddress(account)
            except:
                logging.error("E: given index account does not exist, check .eblocpoa/keystore")
        else:
            logging.error(f"E: Invalid account {address} is provided")

    def _get_balance(self, address):
        address = self.w3.toChecksumAddress(address)
        balance_wei = self.w3.eth.get_balance(address)
        return self.w3.fromWei(balance_wei, "ether")

    def get_block_number(self):
        """Retrun block number."""
        return self.w3.eth.blockNumber

    def is_address(self, addr):
        try:
            return self.w3.isAddress(addr)
        except:
            _colorize_traceback()
            raise Web3NotConnected()

    def _get_contract_fname(self) -> str:
        if env.IS_BLOXBERG:
            return f"{env.EBLOCPATH}/broker/eblocbroker/contract_bloxberg.json"
        elif env.IS_EBLOCPOA:
            return f"{env.EBLOCPATH}/broker/eblocbroker/contract_eblocpoa.json"

    def is_contract_exists(self) -> bool:
        try:
            fname = self._get_contract_fname()
            contract = read_json(fname)
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

    ################
    # Transactions #
    ################
    def _process_payment(self, *args):
        ops = {"from": env.PROVIDER_ID, "gas": 4500000}
        if env.IS_BLOXBERG:
            self.brownie_load_accounts()
            return self.eBlocBroker.processPayment(*args, ops)
        else:
            return self.eBlocBroker.functions.processPayment(*args).transact(ops)

    def withdraw(self, account):
        """Withdraw payment."""
        ops = {"from": self.w3.toChecksumAddress(account), "gas": 4500000}
        if env.IS_BLOXBERG:
            self.brownie_load_accounts()
            return self.eBlocBroker.withdraw(ops)
        else:
            return self.eBlocBroker.functions.withdraw().transact(ops)

    def set_job_status_running(self, key, index, job_id, start_time):
        """Set the job status as running."""
        ops = {"from": self.w3.toChecksumAddress(env.PROVIDER_ID), "gas": 4500000}
        if env.IS_BLOXBERG:
            self.brownie_load_accounts()
            return self.eBlocBroker.setJobStatusRunning(key, int(index), int(job_id), int(start_time), ops)
        else:
            return self.eBlocBroker.functions.setJobStatusRunning(
                key, int(index), int(job_id), int(start_time)
            ).transact(ops)

    def register_data(self, *args):
        """Register the dataset hash."""
        ops = {"from": env.PROVIDER_ID, "gas": 4500000}
        if env.IS_BLOXBERG:
            self.brownie_load_accounts()
            return self.eBlocBroker.registerData(*args, ops)
        else:
            return self.eBlocBroker.functions.registerData(*args).transact(ops)

    def set_register_provider(self, *args):
        """Register provider."""
        ops = {"from": env.PROVIDER_ID, "gas": 4500000}
        if env.IS_BLOXBERG:
            self.brownie_load_accounts()
            return self.eBlocBroker.registerProvider(*args, ops)
        else:
            return self.eBlocBroker.functions.registerProvider(*args).transact(ops)

    def _update_provider_info(self, *args):
        ops = {"from": env.PROVIDER_ID, "gas": 4500000}
        if env.IS_BLOXBERG:
            self.brownie_load_accounts()
            return self.eBlocBroker.updateProviderInfo(*args, ops)
        else:
            return self.eBlocBroker.functions.updateProviderInfo(*args).transact(ops)

    def _update_provider_prices(self, *args):
        ops = {"from": env.PROVIDER_ID, "gas": 4500000}
        if env.IS_BLOXBERG:
            self.brownie_load_accounts()
            return self.eBlocBroker.updateProviderPrices(*args, ops)
        else:
            return self.eBlocBroker.functions.updateProviderPrices(*args).transact(ops)

    def _authenticate_orc_id(self, _from, *args):
        ops = {"from": _from, "gas": 4500000}
        if env.IS_BLOXBERG:
            self.brownie_load_accounts()
            return self.eBlocBroker.authenticateOrcID(*args, ops)
        else:
            return self.eBlocBroker.functions.authenticateOrcID(*args).transact(ops)

    def _transfer_ownership(self, _from, new_owner):
        ops = {"from": _from, "gas": 4500000}
        if env.IS_BLOXBERG:
            self.brownie_load_accounts()
            return self.eBlocBroker.transferOwnership(new_owner, ops)
        else:
            return self.eBlocBroker.functions.transferOwnership(new_owner).transact(ops)

    def _refund(self, _from, *args):
        ops = {"from": _from, "gas": 4500000}
        if env.IS_BLOXBERG:
            self.brownie_load_accounts()
            return self.eBlocBroker.refund(*args, ops)
        else:
            return self.eBlocBroker.functions.refund(*args).transact(ops)

    def _register_requester(self, _from, *args):
        ops = {"from": _from, "gas": 4500000}
        if env.IS_BLOXBERG:
            self.brownie_load_accounts()
            return self.eBlocBroker.registerRequester(*args, ops)
        else:
            return self.eBlocBroker.functions.registerRequester(*args).transact(ops)

    def foo(self):
        self.brownie_load_accounts()

    def _submit_job(self, requester, job_price, *args):
        ops = {"from": requester, "value": self.w3.toWei(job_price, "wei"), "gas": 4500000}
        if env.IS_BLOXBERG:
            self.brownie_load_accounts()
            return self.eBlocBroker.submitJob(*args, ops)
        else:
            return self.eBlocBroker.functions.submitJob(*args).transact(ops)

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
        if not isinstance(address, Account):
            address = self.w3.toChecksumAddress(address)

        if env.IS_BLOXBERG:
            return self.eBlocBroker.doesRequesterExist(address)
        else:
            return self.eBlocBroker.functions.doesRequesterExist(address).call()

    def does_provider_exist(self, address) -> bool:
        """Check whether the given provider is registered."""
        if not isinstance(address, Account):
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
        if not isinstance(address, Account):
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

    def get_balance(self, address):
        if not isinstance(address, Account):
            address = self.w3.toChecksumAddress(address)

        if env.IS_BLOXBERG:
            return self.eBlocBroker.balanceOf(address)
        else:
            return self.eBlocBroker.functions.balanceOf(address).call()

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
        if not isinstance(provider_addr, Account):
            provider_addr = self.w3.toChecksumAddress(provider_addr)

        ops = {"from": _from}
        if isinstance(source_code_hash, str):
            source_code_hash = ipfs_to_bytes32(source_code_hash)

        if env.IS_BLOXBERG:
            return self.eBlocBroker.getJobStorageTime(provider_addr, source_code_hash, ops)  ################
        else:
            return self.eBlocBroker.functions.getJobStorageTime(provider_addr, source_code_hash).call(ops)

    def get_received_storage_deposit(self, provider, requester, source_code_hash):
        """Return received storage deposit for the corresponding source code hash."""
        ops = {"from": provider}
        if isinstance(source_code_hash, str):
            source_code_hash = ipfs_to_bytes32(source_code_hash)

        if env.IS_BLOXBERG:
            return self.eBlocBroker.getReceivedStorageDeposit(provider, requester, source_code_hash, ops)
        else:
            return self.eBlocBroker.functions.getReceivedStorageDeposit(provider, requester, source_code_hash).call(ops)


eblocbroker: "Contract" = None
