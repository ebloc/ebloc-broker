#!/usr/bin/python3

import os
import pytest
import sys
from os import path

import brownie
import contract.tests.cfg as _cfg
from broker import cfg, config
from broker.config import setup_logger
from broker.eblocbroker_scripts import Contract
from broker.eblocbroker_scripts.job import Job
from broker.eblocbroker_scripts.utils import Cent
from broker.lib import JOB
from broker.utils import CacheID, StorageID, log, zero_bytes32
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
    balance = _cfg.TOKEN.balanceOf(to)
    if balance:
        _cfg.TOKEN.approve(accounts[0], balance, {"from": to})
        _cfg.TOKEN.transferFrom(to, accounts[0], balance, {"from": _cfg.OWNER})

    assert _cfg.TOKEN.balanceOf(to) == 0
    _cfg.TOKEN.transfer(to, Cent(amount), {"from": _cfg.OWNER})
    _cfg.TOKEN.approve(ebb.address, Cent(amount), {"from": to})


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


def result_check(delta, spent, value, received_sum, refunded_sum):
    if delta == 0:
        delta = int(delta)

    if abs(delta) > 0:
        log("warning: ", end="")

    log(f"spent={spent} , job_price={value} | delta={delta}")
    log(f" * received={received_sum}")
    log(f" * refunded={refunded_sum}")
    assert delta == 0


def test_cost_0():
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
    for data_hash in [
        b"dd0fbccccf7a198681ab838c67b6abcd",
        b"dd0fbccccf7a198681ab838c67b68fbf",
        b"45281dfec4618e5d20570812dea38760",
    ]:
        ebb.registerData(data_hash, Cent("0.0002 usd"), cfg.ONE_HOUR_BLOCK_DURATION, {"from": provider})
        assert ebb.getRegisteredDataPrice(provider, data_hash, 0)[0] == Cent("0.0002 usd")
        mine(1)

    job = Job()
    job.code_hashes = [b"dd0fbccccf7a198681ab838c67b6abcd"]
    job.key = job.code_hashes[0]
    job.cores = [1]
    job.run_time = [60]
    job.data_transfer_ins = [10]
    job.data_transfer_out = 5
    job.storage_ids = [StorageID.IPFS]
    job.cache_types = [CacheID.PUBLIC]
    job.storage_hours = [0]
    job.data_prices_set_block_numbers = [0]
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
    with brownie.reverts():
        ebb.submitJob(
            job.key,
            job.data_transfer_ins,
            args,
            job.storage_hours,
            job.code_hashes,
            {"from": requester},
        )


def test_cost_1():
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
    for data_hash in [b"dd0fbccccf7a198681ab838c67b68fbf", b"45281dfec4618e5d20570812dea38760"]:
        ebb.registerData(data_hash, Cent("0.0002 usd"), cfg.ONE_HOUR_BLOCK_DURATION, {"from": provider})
        assert ebb.getRegisteredDataPrice(provider, data_hash, 0)[0] == Cent("0.0002 usd")
        mine(1)

    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=- job_0
    job = Job()
    job.code_hashes = [
        b"8bac529584c469c34d40ee45caf1f96f",
        b"02440c95f0eff2a76e6ee88627f58778",
        b"dd0fbccccf7a198681ab838c67b68fbf",
        b"45281dfec4618e5d20570812dea38760",
    ]
    job.key = job.code_hashes[0]
    job.cores = [1]
    job.run_time = [60]
    job.data_transfer_ins = [9, 171, 0, 0]
    job.data_transfer_out = 5
    job.storage_ids = [0, 0, 2, 2]
    job.cache_types = [0, 0, 0, 0]
    job.storage_hours = [0, 1, 0, 0]
    job.data_prices_set_block_numbers = [0, 0, 0, 0]
    job_price, cost = job.cost(provider, requester, is_verbose=True, is_ruler=False)
    _args = [
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
    with brownie.reverts():
        _args[6] = [14401]  # job run time upper limit check
        tx = ebb.submitJob(
            job.key,
            job.data_transfer_ins,
            _args,
            job.storage_hours,
            job.code_hashes,
            {"from": requester},
        )

    _args[6] = [60]
    tx = ebb.submitJob(
        job.key,
        job.data_transfer_ins,
        _args,
        job.storage_hours,
        job.code_hashes,
        {"from": requester},
    )
    cost = tx.events["LogJob"]["received"]
    log(f"estimated_cost={cost}")
    assert cost == job_price
    assert Cent(_cfg.TOKEN.balanceOf(requester)) == 0
    output = ebb.getJobInfo(provider, job.key, 0, 0)
    print(output)
    assert int(output[-2] / _prices.get()[-1]) >= job.data_transfer_ins[0]
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

    # -----------------------------------------------------------------------------------
    start_ts = 1579524978
    tx = ebb.setJobStateRunning(job.code_hashes[0], 0, 0, start_ts, {"from": provider})
    elapsed = 7
    dt_in = 140
    dt_out = 0
    _args = [
        0,  # index
        0,  # jobId
        1681003991,  # endTimestamp
        dt_in,
        dt_out,
        elapsed,
        job.cores,
        [60],
        JOB.TYPE["SINGLE"],
    ]
    tx = ebb.processPayment(job.code_hashes[0], _args, zero_bytes32, {"from": provider})
    assert _cfg.TOKEN.balanceOf(provider) == 0
    assert _cfg.TOKEN.allowance(ebb.address, provider) > 0
    assert _cfg.TOKEN.allowance(ebb.address, requester) > 0

    log_process_payment = dict(tx.events["LogProcessPayment"])
    if log_process_payment["resultIpfsHash"] == _cfg.ZERO:
        del log_process_payment["resultIpfsHash"]

    received_sum = log_process_payment["receivedCent"]
    refunded_sum = log_process_payment["refundedCent"]
    assert received_sum == _cfg.TOKEN.allowance(ebb.address, provider)
    assert refunded_sum == _cfg.TOKEN.allowance(ebb.address, requester)
    _cfg.TOKEN.transferFrom(ebb.address, provider, received_sum, {"from": provider})
    _cfg.TOKEN.transferFrom(ebb.address, requester, refunded_sum, {"from": requester})

    assert _cfg.TOKEN.balanceOf(provider) == received_sum
    assert _cfg.TOKEN.balanceOf(requester) == refunded_sum

    total_spent = received_sum + refunded_sum
    spent = Cent(abs(total_spent + paid_storage)).to("cent")
    value = Cent(abs(job_price)).to("cent")
    delta = value.__sub__(spent)  # type: ignore
    if verbose:
        log("log_process_payment=", end="")
        log(log_process_payment)

    result_check(delta, spent, value, received_sum, refunded_sum)

    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=- job_1
    job = Job()
    job.code_hashes = [
        b"8bac529584c469c34d40ee45caf1f96f",
        b"02440c95f0eff2a76e6ee88627f58778",
        b"dd0fbccccf7a198681ab838c67b68fbf",
        b"45281dfec4618e5d20570812dea38760",
    ]
    job.key = job.code_hashes[0]
    job.cores = [1]
    job.run_time = [60]
    job.data_transfer_ins = [9, 171, 0, 0]
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
        job_price + 10000,
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
    cost = tx.events["LogJob"]["received"]
    log(f"estimated_cost={cost}")
    index = 1
    output = ebb.getJobInfo(provider, job.key, index, 0)
    print(output)
    calculated_cache_cost = output[-2]
    assert calculated_cache_cost > 0
    assert cost == job_price
    assert Cent(_cfg.TOKEN.balanceOf(requester)) == 0
    considered_cache = int(calculated_cache_cost / _prices.get()[-1])
    assert considered_cache >= job.data_transfer_ins[0]
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

    # ----------------------------------------------------------------------------------------------
    start_ts = 1579524978
    tx = ebb.setJobStateRunning(job.code_hashes[0], index, 0, start_ts, {"from": provider})
    elapsed = 7
    dt_in = 9  # if its > 9 fails
    dt_out = 0
    #  index jobId endTimestamp
    #      \   |       |
    args = [index, 0, 1681003991, dt_in, dt_out, elapsed, job.cores, [60], JOB.TYPE["SINGLE"]]
    tx = ebb.processPayment(job.code_hashes[0], args, zero_bytes32, {"from": provider})
    log_process_payment = dict(tx.events["LogProcessPayment"])
    if log_process_payment["resultIpfsHash"] == _cfg.ZERO:
        del log_process_payment["resultIpfsHash"]

    received_sum = log_process_payment["receivedCent"]
    refunded_sum = log_process_payment["refundedCent"]
    total_spent = received_sum + refunded_sum
    spent = Cent(abs(total_spent + paid_storage)).to("cent")
    value = Cent(abs(job_price)).to("cent")
    delta = value.__sub__(spent)  # type: ignore
    if verbose:
        log("log_process_payment=", end="")
        log(log_process_payment)

    result_check(delta, spent, value, received_sum, refunded_sum)


def test_cost_2():
    _prices = Prices()
    _prices.set_core_min("0.001 usd")
    _prices.set_data_transfer("0.0001 cent")
    _prices.set_storage("0.0001 cent")
    _prices.set_cache("0.0001 cent")
    #
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
    job.data_transfer_ins = [5, 375, 0, 0]
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
    cost = tx.events["LogJob"]["received"]
    log(f"estimated_cost={cost}")
    assert cost == job_price
    assert Cent(_cfg.TOKEN.balanceOf(requester)) == 0
    output = ebb.getJobInfo(provider, job.key, 0, 0)
    print(output)
    assert int(output[-2] / _prices.get()[-1]) >= job.data_transfer_ins[0]
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

    # ----------------------------------------------------------------------------------------------
    start_ts = 1579524978
    tx = ebb.setJobStateRunning(job.code_hashes[0], 0, 0, start_ts, {"from": provider})
    elapsed = 7
    dt_in = 0
    dt_out = 4
    #  index jobId endTimestamp
    #      \   |       |
    args = [
        0,
        0,
        1681003991,
        dt_in,
        dt_out,
        elapsed,
        job.cores,
        [60],
        JOB.TYPE["SINGLE"],
    ]
    tx = ebb.processPayment(job.code_hashes[0], args, zero_bytes32, {"from": provider})
    log_process_payment = dict(tx.events["LogProcessPayment"])
    if log_process_payment["resultIpfsHash"] == _cfg.ZERO:
        del log_process_payment["resultIpfsHash"]

    received_sum = log_process_payment["receivedCent"]
    refunded_sum = log_process_payment["refundedCent"]
    total_spent = received_sum + refunded_sum
    spent = Cent(abs(total_spent + paid_storage)).to("cent")
    value = Cent(abs(job_price)).to("cent")
    delta = value.__sub__(spent)  # type: ignore
    if verbose:
        log("log_process_payment=", end="")
        log(log_process_payment)

    result_check(delta, spent, value, received_sum, refunded_sum)


def test_cost_3():
    _prices = Prices()
    _prices.set_core_min("0.001 usd")
    _prices.set_data_transfer("0.0001 cent")
    _prices.set_storage("0.0001 cent")
    _prices.set_cache("0.0001 cent")
    #
    prices = _prices.get()
    provider = accounts[1]
    requester = accounts[2]
    register_provider(available_core=4, prices=prices)
    register_requester(requester)
    for data_hash in [b"dd0fbccccf7a198681ab838c67b68fbf", b"45281dfec4618e5d20570812dea38760"]:
        ebb.registerData(data_hash, Cent("0.0002 usd"), cfg.ONE_HOUR_BLOCK_DURATION, {"from": provider})
        assert ebb.getRegisteredDataPrice(provider, data_hash, 0)[0] == Cent("0.0002 usd")
        mine(1)

    job = Job()
    job.code_hashes = [
        b"8bac529584c469c34d40ee45caf1f96f",
        b"02440c95f0eff2a76e6ee88627f58778",
        b"dd0fbccccf7a198681ab838c67b68fbf",
        b"45281dfec4618e5d20570812dea38760",
    ]
    job.key = job.code_hashes[0]
    job.cores = [1]
    job.run_time = [60]
    job.data_transfer_ins = [9, 1000, 0, 0]
    job.data_transfer_out = 5
    job.storage_ids = [3, 3, 2, 2]
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
    cost = tx.events["LogJob"]["received"]
    log(f"estimated_cost={cost}")
    assert cost == job_price
    assert Cent(_cfg.TOKEN.balanceOf(requester)) == 0
    output = ebb.getJobInfo(provider, job.key, 0, 0)
    print(output)
    assert int(output[-2] / _prices.get()[-1]) >= job.data_transfer_ins[0]
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

    # ----------------------------------------------------------------------------------------------
    start_ts = 1579524978
    tx = ebb.setJobStateRunning(job.code_hashes[0], 0, 0, start_ts, {"from": provider})
    elapsed = 3
    dt_in = 404
    dt_out = 0
    #  index jobId endTimestamp
    #      \   |       |
    args = [0, 0, 1681003991, dt_in, dt_out, elapsed, job.cores, [60], JOB.TYPE["SINGLE"]]
    tx = ebb.processPayment(job.code_hashes[0], args, zero_bytes32, {"from": provider})
    log_process_payment = dict(tx.events["LogProcessPayment"])
    if log_process_payment["resultIpfsHash"] == _cfg.ZERO:
        del log_process_payment["resultIpfsHash"]

    received_sum = log_process_payment["receivedCent"]
    refunded_sum = log_process_payment["refundedCent"]
    total_spent = received_sum + refunded_sum
    spent = Cent(abs(total_spent + paid_storage)).to("cent")
    value = Cent(abs(job_price)).to("cent")
    delta = value.__sub__(spent)  # type: ignore
    if verbose:
        log("log_process_payment=", end="")
        log(log_process_payment)

    result_check(delta, spent, value, received_sum, refunded_sum)
