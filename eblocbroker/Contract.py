#!/usr/bin/env python3

from config import Web3NotConnected, env
from utils import _colorize_traceback, read_json


class Contract:
    def __init__(self):
        from imports import connect

        self.eBlocBroker, self.w3 = connect()

    # Imported methods
    from eblocbroker.authenticate_orc_id import authenticate_orc_id
    from eblocbroker.get_provider_info import get_provider_info
    from eblocbroker.process_payment import process_payment
    from eblocbroker.submit_job import submit_job, check_before_submit
    from eblocbroker.get_job_info import get_job_info, update_job_cores, get_job_source_code_hashes
    from eblocbroker.get_requester_info import get_requester_info
    from eblocbroker.log_job import run_log_cancel_refund, run_log_job
    from eblocbroker.register_provider import register_provider
    from eblocbroker.refund import refund
    from eblocbroker.register_requester import register_requester
    from eblocbroker.update_provider_info import update_provider_info
    from eblocbroker.update_provider_prices import update_provider_prices
    from eblocbroker.transfer_ownership import transfer_ownership

    def get_job_size(self, provider, key):
        return self.eBlocBroker.call().getJobSize(provider, key)

    def is_orcid_verified(self, requester):
        return self.eBlocBroker.functions.isOrcIDVerified(requester).call()

    def does_requester_exist(self, address):
        address = self.w3.toChecksumAddress(address)
        return self.eBlocBroker.functions.doesRequesterExist(address).call()

    def does_provider_exist(self, address):
        address = self.w3.toChecksumAddress(address)
        return self.eBlocBroker.functions.doesProviderExist(address).call()

    def is_owner(self, addr) -> bool:
        # Checks if the given address is the owner of the contract
        return addr.lower() == self.get_owner().lower()

    def get_owner(self):
        return self.eBlocBroker.functions.getOwner().call()

    def get_balance(self, address):
        address = self.w3.toChecksumAddress(address)
        return self.eBlocBroker.functions.balanceOf(address).call()

    def get_block_number(self):
        return self.w3.eth.blockNumber

    def get_deployed_block_number(self):
        try:
            contract = read_json(f"{env.HOME}/eBlocBroker/eblocbroker/contract.json")
        except:
            _colorize_traceback()
            return False

        return self.w3.eth.getTransaction(contract["txHash"]).blockNumber

    def is_web3_connected(self):
        return self.w3.isConnected()

    def withdraw(self, account):
        try:
            account = self.w3.toChecksumAddress(account)
            tx = self.eBlocBroker.functions.withdraw().transact({"from": account, "gas": 50000})
            return tx.hex()
        except Exception:
            _colorize_traceback()
            raise

    def set_job_status_running(self, key, index, job_id, startTime):
        try:
            tx = self.eBlocBroker.functions.setJobStatusRunning(key, int(index), int(job_id), int(startTime)).transact(
                {"from": self.w3.toChecksumAddress(env.PROVIDER_ID), "gas": 4500000}
            )
            return tx.hex()
        except Exception:
            _colorize_traceback()
            raise

    def get_providers(self):
        try:
            return self.eBlocBroker.functions.getProviders().call()
        except:
            _colorize_traceback()
            raise Web3NotConnected()

    def register_data(self, source_code_hash, price, commitmentBlockDuration: int):
        try:
            tx = self.eBlocBroker.functions.registerData(source_code_hash, price, commitmentBlockDuration).transact(
                {"from": env.PROVIDER_ID, "gas": 100000}
            )
            return tx.hex()
        except Exception:
            _colorize_traceback()
            raise

    def is_address(self, addr):
        try:
            return self.w3.isAddress(addr)
        except:
            _colorize_traceback()
            raise Web3NotConnected()

    def get_job_storage_time(self, addr, source_code_hash):
        provider_address = self.w3.toChecksumAddress(addr)
        ret = self.eBlocBroker.call().getJobStorageTime(provider_address, source_code_hash)
        return ret[0], ret[1]

    def is_contract_exists(self):
        try:
            contract = read_json(f"{env.EBLOCPATH}/eblocbroker/contract.json")
        except:
            _colorize_traceback()
            raise

        contract_address = self.w3.toChecksumAddress(contract["address"])
        if self.w3.eth.getCode(contract_address) == "0x" or self.w3.eth.getCode(contract_address) == b"":
            raise

    def get_provider_receipt_node(self, provider_address, index):
        return self.eBlocBroker.functions.getProviderReceiptNode(provider_address, index).call()

    def get_provider_receipt_size(self, address):
        address = self.w3.toChecksumAddress(address)
        return self.eBlocBroker.functions.getProviderReceiptSize(address).call()

    def get_transaction_receipt(self, tx):
        """
        doc: https://web3py.readthedocs.io/en/stable/web3.eth.html#web3.eth.Eth.getTransactionReceipt
        Returns the transaction receipt specified by transactionHash.
        If the transaction has not yet been mined returns 'None'
        """
        return self.w3.eth.getTransactionReceipt(tx)


eblocbroker = Contract()
