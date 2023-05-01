#!/usr/bin/python3

import os
import pytest
import sys
from os import path

import contract.tests.cfg as _cfg
from broker import cfg, config
from broker.config import setup_logger
from broker.eblocbroker_scripts import Contract
from broker.eblocbroker_scripts.job import Job
from broker.eblocbroker_scripts.utils import Cent
from broker.utils import log, zero_bytes32
from brownie import accounts, web3
from brownie.network.state import Chain
from contract.scripts.lib import mine, new_test
from contract.tests.test_overall_eblocbroker import register_provider, register_requester  # , set_transfer

# from brownie.test import given, strategy

COMMITMENT_BLOCK_NUM = 600
verbose = True
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


class Prices:
    def __init__(self):
        self.core_min: "Cent" = 0
        self.data_transfer: "Cent" = 0
        self.storage: "Cent" = 0
        self.cache_min: "Cent" = 0

    def set_core_min(self, value):
        self.core_min = Cent(str(value))

    def set_data_transfer(self, value):
        self.data_transfer = Cent(str(value))

    def set_storage(self, value):
        self.storage = Cent(str(value))

    def set_cache(self, value):
        self.cache_min = Cent(str(value))

    def get(self):
        return [self.core_min, self.data_transfer, self.storage, self.cache_min]


def _transfer(to, amount):
    ebb.transfer(to, Cent(amount), {"from": _cfg.OWNER})


def set_transfer(to, amount):
    """Empty balance and transfer given amount."""
    balance = ebb.balanceOf(to)
    ebb.approve(accounts[0], balance, {"from": to})
    ebb.transferFrom(to, accounts[0], balance, {"from": _cfg.OWNER})
    assert ebb.balanceOf(to) == 0
    ebb.transfer(to, Cent(amount), {"from": _cfg.OWNER})


@pytest.fixture(scope="module", autouse=True)
def my_own_session_run_at_beginning(_Ebb):
    global Ebb, chain, ebb  # noqa
    cfg.IS_BROWNIE_TEST = True
    config.Ebb = Ebb = Contract.Contract(is_brownie=True)
    config.ebb = _Ebb
    cfg.Ebb.eBlocBroker = Contract.eblocbroker.eBlocBroker = _Ebb
    _cfg.ebb = ebb = _Ebb
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
            assert key in res, f"{key} does no exist in price keys({res}) for the registered data{code_hash}"


def remove_zeros_gpg_fingerprint(_gpg_fingerprint):
    return str(_gpg_fingerprint).replace("0x000000000000000000000000", "").upper()


def get_block_number():
    log(f"bn={web3.eth.blockNumber} | bn_for_contract={web3.eth.blockNumber + 1}")
    return web3.eth.blockNumber


def get_block_timestamp():
    return web3.eth.getBlock(get_block_number()).timestamp


def test_cost():
    _prices = Prices()
    _prices.set_core_min("0.001 usd")
    _prices.set_data_transfer("0.0001 cent")
    _prices.set_storage("0.0001 cent")
    _prices.set_cache("0.0001 cent")
    prices = _prices.get()
    provider = accounts[1]
    requester = accounts[2]
    register_provider(available_core=4, prices=prices)
    register_requester(requester)
    for data_hash in [b"0d6c3288ef71d89fb93734972d4eb903", b"4613abc322e8f2fdeae9a5dd10f17540"]:
        ebb.registerData(data_hash, Cent("0.0002 usd"), cfg.ONE_HOUR_BLOCK_DURATION, {"from": provider})
        assert ebb.getRegisteredDataPrice(provider, data_hash, 0)[0] == Cent("0.0002 usd")
        mine(1)

    job = Job()
    job.code_hashes = [
        b"0000abc322e8f2fdeae9a5dd10f17540",
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
    job.data_prices_set_block_numbers = [0, 0, 0, 0]
    job_price, cost = job.cost(provider, requester, is_verbose=True, is_ruler=False)
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
    assert Cent(ebb.balanceOf(requester)) == 0

    paid_storage = 0
    counter = 0
    while True:
        try:
            log_data_storage_request = dict(tx.events["LogDataStorageRequest"][counter])
            counter += 1
            paid_storage += log_data_storage_request["paid"]
            if verbose:
                log(log_data_storage_request)
        except:
            break

    #
    start_ts = 1579524978
    tx = ebb.setJobStateRunning(job.code_hashes[0], 0, 0, start_ts, {"from": provider})
    args = [0, 0, 1681003991, 0, 0, 7, job.cores, [60], True]
    tx = ebb.processPayment(job.code_hashes[0], args, zero_bytes32, {"from": provider})
    log_process_payment = dict(tx.events["LogProcessPayment"])
    if log_process_payment["resultIpfsHash"] == _cfg.ZERO:
        del log_process_payment["resultIpfsHash"]

    received_sum = log_process_payment["receivedCent"]
    refunded_sum = log_process_payment["refundedCent"]
    total_spent = received_sum + refunded_sum
    spent = Cent(abs(total_spent + paid_storage)).to("cent")
    value = Cent(abs(job_price)).to("cent")
    delta = value.__sub__(spent)  # noqa
    if verbose:
        log("log_process_payment=", end="")
        log(log_process_payment)

    if delta == 0:
        delta = int(delta)

    if abs(delta) > 0:
        log("warning: ")

    log(f"spent={spent} , value={value} | delta={delta}")
    log(f" * received={received_sum}")
    log(f" * refunded={refunded_sum}")
    assert delta == 0
