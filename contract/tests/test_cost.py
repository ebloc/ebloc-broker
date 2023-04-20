#!/usr/bin/python3

import os
import sys
from os import path

import pytest

from broker import cfg, config
from broker.config import setup_logger
from broker.eblocbroker_scripts import Contract
from broker.eblocbroker_scripts.job import Job
from broker.eblocbroker_scripts.utils import Cent
from broker.utils import CacheType, StorageID, ipfs_to_bytes32, log
from brownie import accounts, web3
from brownie.network.state import Chain
from contract.scripts.lib import gas_costs, mine, new_test
from contract.tests.test_overall_eblocbroker import register_provider, register_requester, set_transfer

# from brownie.test import given, strategy

COMMITMENT_BLOCK_NUM = 600
Contract.eblocbroker = Contract.Contract(is_brownie=True)

setup_logger("", True)
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
cwd = os.getcwd()
provider_gmail = "provider_test@gmail.com"
fid = "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu"

GPG_FINGERPRINT = "0359190A05DF2B72729344221D522F92EFA2F330"
ipfs_address = "/ip4/79.123.177.145/tcp/4001/ipfs/QmWmZQnb8xh3gHf9ZFmVQC4mLEav3Uht5kHJxZtixG3rsf"
Ebb = None
chain = None
ebb = None
OWNER = None


def append_gas_cost(func_n, tx):
    gas_costs[func_n].append(tx.__dict__["gas_used"])


def _transfer(to, amount):
    ebb.transfer(to, Cent(amount), {"from": OWNER})


@pytest.fixture(scope="module", autouse=True)
def my_own_session_run_at_beginning(_Ebb):
    global Ebb  # noqa
    global chain  # noqa
    global ebb  # noqa
    global OWNER

    cfg.IS_BROWNIE_TEST = True
    config.Ebb = Ebb = Contract.Contract(is_brownie=True)
    config.ebb = _Ebb
    cfg.Ebb.eBlocBroker = Contract.eblocbroker.eBlocBroker = _Ebb
    ebb = _Ebb
    Ebb.w3 = web3
    if not config.chain:
        config.chain = Chain()

    chain = config.chain
    OWNER = accounts[0]


@pytest.fixture(autouse=True)
def run_around_tests():
    new_test()


def check_price_keys(price_keys, provider, code_hash):
    res = ebb.getRegisteredDataBlockNumbers(provider, code_hash)
    for key in price_keys:
        if key > 0:
            assert key in res, f"{key} does no exist in price keys({res}) for the registered data{code_hash}"


def remove_zeros_gpg_fingerprint(_gpg_fingerprint):
    return str(_gpg_fingerprint).replace("0x000000000000000000000000", "").upper()


def get_block_number():
    log(f"bn={web3.eth.blockNumber} | contract_bn={web3.eth.blockNumber + 1}")
    return web3.eth.blockNumber


def get_block_timestamp():
    return web3.eth.getBlock(get_block_number()).timestamp


def test_cost():
    p_core_min = Cent("0.001 usd")
    p_data_transfer = Cent("0.0001 cent")
    p_storage = Cent("0.0001 cent")
    p_cache = Cent("0.0001 cent")
    prices = [p_core_min, p_data_transfer, p_storage, p_cache]
    provider = accounts[1]
    requester = accounts[2]
    register_provider(_available_core=4, prices=prices)
    register_requester(requester)

    job = Job()
    # job_key = "QmQv4AAL8DZNxZeK3jfJGJi63v1msLMZGan7vSsCDXzZud"
    job.code_hashes = [
        "QmeHL7LvHwQs4xrzPqvkA8fH9T8XGya7BgiLKWb7XG6w71",
        b"9613abc322e8f2fdeae9a5dd10f17540",
        b"0d6c3288ef71d89fb93734972d4eb903",
        b"4613abc322e8f2fdeae9a5dd10f17540",
    ]
    job.key = job.code_hashes[0]
    job.cores = [1]
    job.run_time = [60]
    job.data_transfer_ins = [1, 375, 0, 0]
    job.data_transfer_out = 5
    job.storage_ids = [0, 0, 2, 2]
    job.cache_types = [0, 0, 0, 0]
    job.storage_hours = [0, 1, 0, 0]
    job.data_prices_set_block_numbers = [0, 0]
    job_price, cost = job.cost(provider, requester)
    args = [
        provider,
        ebb.getProviderSetBlockNumbers(provider)[-1],
        job.storage_ids,
        job.cache_types,
        job.data_prices_set_block_numbers,
        job.cores,
        job.run_time,
        job.data_transfer_out,
        job_price,
    ]
    set_transfer(requester, Cent(job_price))
    tx = ebb.submitJob(
        job.key,
        job.data_transfer_ins,
        args,
        job.storage_hours,
        job.code_hashes,
        {"from": requester},
    )
