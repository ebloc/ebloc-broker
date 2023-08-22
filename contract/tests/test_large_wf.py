#!/usr/bin/python3

import os
import pytest
import sys
from os import path

import brownie
import contract.tests.cfg as _cfg
from broker import cfg, config
from broker._utils._log import console_ruler
from broker.config import setup_logger
from broker.eblocbroker_scripts import Contract
from broker.eblocbroker_scripts.job import Job
from broker.eblocbroker_scripts.utils import Cent
from broker.lib import JOB
from broker.utils import CacheID, StorageID, ipfs_to_bytes32, log
from brownie import accounts, web3
from brownie.network.state import Chain
from contract.scripts.lib import gas_costs, mine, new_test
from contract.tests.test_overall_eblocbroker import register_provider, register_requester

# from brownie.test import given, strategy

COMMITMENT_BLOCK_NUM = 600
Contract.eblocbroker = Contract.Contract(is_brownie=True)

setup_logger("", True)
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
cwd = os.getcwd()
provider_gmail = "provider_test@gmail.com"
fid = "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu"

price_core_min = Cent("0.0001 usd")
price_storage = Cent("0.00001 cent")
price_cache = Cent("0.00001 cent")
price_data_transfer = Cent("0.0001 cent")

prices = [price_core_min, price_data_transfer, price_storage, price_cache]

GPG_FINGERPRINT = "0359190A05DF2B72729344221D522F92EFA2F330"
ipfs_address = "/ip4/79.123.177.145/tcp/4001/ipfs/QmWmZQnb8xh3gHf9ZFmVQC4mLEav3Uht5kHJxZtixG3rsf"
Ebb = None
chain = None
ebb = None


def print_gas_costs():
    """Cleanup a testing directory once we are finished."""
    for k, v in gas_costs.items():
        if v:
            # print(f"{k} => {v}")
            log(f"==> {k} => {int(sum(v) / len(v))}")


def append_gas_cost(func_n, tx):
    gas_costs[func_n].append(tx.__dict__["gas_used"])


def _transfer(to, amount):
    """Empty balance and transfer given amount."""
    balance = _cfg.TOKEN.balanceOf(to)
    if balance:
        _cfg.TOKEN.approve(accounts[0], balance, {"from": to})
        _cfg.TOKEN.transferFrom(to, accounts[0], balance, {"from": _cfg.OWNER})

    assert _cfg.TOKEN.balanceOf(to) == 0
    _cfg.TOKEN.transfer(to, Cent(amount), {"from": _cfg.OWNER})
    _cfg.TOKEN.approve(ebb.address, Cent(amount), {"from": to})


@pytest.fixture(scope="module", autouse=True)
def my_own_session_run_at_beginning(_Ebb):
    global Ebb  # noqa
    global chain  # noqa
    global ebb  # noqa

    cfg.IS_BROWNIE_TEST = True
    config.Ebb = Ebb = Contract.Contract(is_brownie=True)
    config.ebb = _Ebb
    cfg.Ebb.eBlocBroker = Contract.eblocbroker.eBlocBroker = _Ebb
    ebb = _Ebb
    Ebb.w3 = web3
    if not config.chain:
        config.chain = Chain()

    chain = config.chain
    _cfg.OWNER = accounts[0]


@pytest.fixture(autouse=True)
def run_around_tests():
    new_test()


def check_price_keys(price_keys, provider, code_hash):
    res = ebb.getRegisteredDataBlockNumbers(provider, code_hash)
    for key in price_keys:
        if key > 0:
            assert key in res, f"{key} does no exist in price keys={res} for the registered data{code_hash}"


def get_bn():
    log(f"block_number={web3.eth.blockNumber} | contract_bn={web3.eth.blockNumber + 1}")
    return web3.eth.blockNumber


def get_block_timestamp():
    return web3.eth.getBlock(get_bn()).timestamp


@pytest.mark.skip(reason="no way of currently testing this")
def test_dummy():
    pass


def test_workflow():
    job = Job()
    provider = accounts[1]
    requester = accounts[2]
    register_provider(available_core=128)
    register_requester(requester)
