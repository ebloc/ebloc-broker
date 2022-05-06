#!/usr/bin/env python3

import os
import sys
from os import path

import pytest

from broker import cfg, config
from broker._utils._log import br, console_ruler, log
from broker.config import setup_logger
from broker.eblocbroker_scripts import Contract
from broker.eblocbroker_scripts.job import Job
from broker.utils import CacheType, StorageID
from brownie import accounts, rpc, web3
from brownie.network.state import Chain
from contract.scripts.lib import mine, new_test
from contract.tests.test_overall_eblocbroker import register_provider, register_requester

Contract.eblocbroker = Contract.Contract(is_brownie=True)


# from brownie.test import given, strategy
setup_logger("", True)
config.logging.propagate = False

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
cwd = os.getcwd()

provider_gmail = "provider@gmail.com"
available_core_num = 128
price_core_min = 1
price_data_transfer = 1
price_storage = 1
price_cache = 1
prices = [price_core_min, price_data_transfer, price_storage, price_cache]

GPG_FINGERPRINT = "0359190A05DF2B72729344221D522F92EFA2F330"
ipfs_address = "/ip4/79.123.177.145/tcp/4001/ipfs/QmWmZQnb8xh3gHf9ZFmVQC4mLEav3Uht5kHJxZtixG3rsf"

provider = None
requester = None
ebb = None
chain = None


@pytest.fixture(scope="module", autouse=True)
def my_own_session_run_at_beginning(_Ebb):
    global Ebb  # noqa
    global chain  # noqa
    global ebb  # noqa

    cfg.IS_BROWNIE_TEST = True
    config.Ebb = Ebb = Contract.Contract(is_brownie=True)
    config.ebb = _Ebb
    Contract.eblocbroker.eBlocBroker = _Ebb
    ebb = _Ebb
    Ebb.w3 = web3
    if not config.chain:
        config.chain = Chain()

    chain = config.chain


# @pytest.fixture(scope="module", autouse=True)
# def my_own_session_run_at_beginning(_Ebb):
#     global ebb
#     global chain
#     cfg.IS_BROWNIE_TEST = True
#     config.w3 = web3
#     ebb = Contract.eblocbroker.eBlocBroker = config.ebb = _Ebb
#     if not config.chain:
#         config.chain = Chain()

#     chain = config.chain


@pytest.fixture(autouse=True)
def run_around_tests():
    new_test()


def check_list(is_print=True):
    # initial (0, 0) root node is ignored
    _length = ebb.getProviderReceiptNode(provider, 0)[0] - 1
    if is_print:
        print(f"length={_length}")

    for idx in range(0, _length):
        output = ebb.getProviderReceiptNode(provider, idx)
        if is_print:
            log(f"{output[1]} {output[2]}")

    _list = []
    carried_sum = 0
    for idx in range(0, _length):
        output = ebb.getProviderReceiptNode(provider, idx)
        if output[1] != 0:
            carried_sum += output[2]

        assert (
            carried_sum <= available_core_num
        ), f"carried sum={carried_sum} exceed available_core_num={available_core_num}"

        _list.append(output[1])

    assert _list == sorted(_list, reverse=True)
    assert carried_sum == 0


def check_price_keys(price_keys, provider, code_hash):
    res = ebb.getRegisteredDataBlockNumbers(provider, code_hash)
    for key in price_keys:
        if key > 0:
            assert key in res, f"{key} does no exist in price keys({res}) for the registered data{code_hash}"


def submit_receipt(index, cores, start_timestamp, end_timestamp, elapsed_time, is_print=True):
    text = f"{start_timestamp},{end_timestamp}"
    log(f"==> {br(text)} cores={cores}")
    job = Job()
    job.code_hashes = [b"8b3e98abb65d0c1aceea8d606fc55403"]
    job.key = job.code_hashes[0]
    job.index = index
    job._id = 0
    job.cores = cores
    job.run_time = [1]
    job.data_transfer_ins = [1]
    job.data_transfer_out = 1
    job.storage_ids = [StorageID.EUDAT.value]
    job.cache_types = [CacheType.PUBLIC.value]
    job.storage_hours = [0]
    job.data_prices_set_block_numbers = [0]
    job_price, _cost = job.cost(provider, requester)
    provider_price_block_number = ebb.getProviderSetBlockNumbers(provider)[-1]
    args = [
        provider,
        provider_price_block_number,
        job.storage_ids,
        job.cache_types,
        job.data_prices_set_block_numbers,
        job.cores,
        job.run_time,
        job.data_transfer_out,
    ]
    tx = ebb.submitJob(
        job.key,
        job.data_transfer_ins,
        args,
        job.storage_hours,
        job.code_hashes,
        {"from": requester, "value": web3.toWei(job_price, "gwei")},
    )

    tx = ebb.setJobStateRunning(job.key, job.index, job._id, start_timestamp, {"from": provider})
    rpc.sleep(60)
    mine(5)
    data_transfer_in = 0
    data_transfer_out = 0
    args = [job.index, job._id, end_timestamp, data_transfer_in, data_transfer_out, elapsed_time, job.cores, [1], True]
    tx = ebb.processPayment(job.key, args, "", {"from": provider})
    if is_print:
        log(f"==> process_payment received_gas_used={tx.__dict__['gas_used']}")

    # received_sum = tx.events["LogProcessPayment"]["receivedGwei"]
    # refunded_sum = tx.events["LogProcessPayment"]["refundedGwei"]
    # withdraw(provider, received_sum)
    # withdraw(requester, refunded_sum)
    check_list(is_print)
    if is_print:
        console_ruler(character="-=")

    return tx


def test_submit_job_gas():
    global provider
    global requester
    mine(1)
    mine(5)

    provider = accounts[0]
    requester = accounts[1]

    register_provider(100)
    register_requester(requester)

    start_timestamp = 10
    end_timestamp = 20
    cores = [127]
    index = 0
    submit_receipt(index, cores, start_timestamp, end_timestamp, elapsed_time=1)
    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    start_timestamp = 10
    end_timestamp = 25
    cores = [1]
    index = 1
    submit_receipt(index, cores, start_timestamp, end_timestamp, elapsed_time=1)
    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    start_timestamp = 11
    end_timestamp = 25
    cores = [1]
    index = 2
    tx = submit_receipt(index, cores, start_timestamp, end_timestamp, elapsed_time=1)
    gas_base = int(tx.__dict__["gas_used"])
    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    start_timestamp = 8
    end_timestamp = 9
    cores = [65]
    index = 3
    tx = submit_receipt(index, cores, start_timestamp, end_timestamp, elapsed_time=1)
    gas_end = int(tx.__dict__["gas_used"])
    check_list()
    log(f"==> gas_cost_for_iteration={gas_end - gas_base}")
    # TODO: : revert on tx check


def test_test1():
    global provider
    global requester

    provider = accounts[0]
    requester = accounts[1]

    register_provider(100)
    register_requester(requester)

    start_timestamp = 10
    end_timestamp = 20
    cores = [1]
    index = 0
    submit_receipt(index, cores, start_timestamp, end_timestamp, elapsed_time=1)
    # -------------------
    start_timestamp = 27
    end_timestamp = 35
    cores = [1]
    index = 1
    submit_receipt(index, cores, start_timestamp, end_timestamp, elapsed_time=1)
    # -------------------
    start_timestamp = 30
    end_timestamp = 45
    cores = [1]
    index = 2
    submit_receipt(index, cores, start_timestamp, end_timestamp, elapsed_time=1)
    # -------------------
    start_timestamp = 30
    end_timestamp = 45
    cores = [1]
    index = 3
    submit_receipt(index, cores, start_timestamp, end_timestamp, elapsed_time=1)
    # -------------------
    start_timestamp = 27
    end_timestamp = 30
    cores = [120]
    index = 4
    submit_receipt(index, cores, start_timestamp, end_timestamp, elapsed_time=1)


def test_test2():
    global provider
    global requester

    provider = accounts[0]
    requester = accounts[1]

    register_provider(100)
    register_requester(requester)

    start_timestamp = 10
    end_timestamp = 20
    cores = [1]
    index = 0
    submit_receipt(index, cores, start_timestamp, end_timestamp, elapsed_time=1)
    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    start_timestamp = 10
    end_timestamp = 20
    cores = [128]
    index += 1
    submit_receipt(index, cores, start_timestamp, end_timestamp, elapsed_time=1)
    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    start_timestamp = 9
    end_timestamp = 19
    cores = [128]
    index += 1
    submit_receipt(index, cores, start_timestamp, end_timestamp, elapsed_time=1)
    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    start_timestamp = 11
    end_timestamp = 21
    cores = [128]
    index += 1
    submit_receipt(index, cores, start_timestamp, end_timestamp, elapsed_time=1)
    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    start_timestamp = 15
    end_timestamp = 25
    cores = [1]
    index += 1
    submit_receipt(index, cores, start_timestamp, end_timestamp, elapsed_time=1)
    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    start_timestamp = 8
    end_timestamp = 9
    cores = [1]
    index += 1
    submit_receipt(index, cores, start_timestamp, end_timestamp, elapsed_time=1)
    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    start_timestamp = 40
    end_timestamp = 45
    cores = [1]
    index += 1
    submit_receipt(index, cores, start_timestamp, end_timestamp, elapsed_time=1)
    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    start_timestamp = 40
    end_timestamp = 45
    cores = [126]
    index += 1
    submit_receipt(index, cores, start_timestamp, end_timestamp, elapsed_time=1)
    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    start_timestamp = 41
    end_timestamp = 45
    cores = [1]
    index += 1
    submit_receipt(index, cores, start_timestamp, end_timestamp, elapsed_time=1)
    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    start_timestamp = 39
    end_timestamp = 41
    cores = [1]
    index += 1
    submit_receipt(index, cores, start_timestamp, end_timestamp, elapsed_time=1)
    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    start_timestamp = 26
    end_timestamp = 39
    cores = [1]
    index += 1
    submit_receipt(index, cores, start_timestamp, end_timestamp, elapsed_time=1)
    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    start_timestamp = 20
    end_timestamp = 38
    cores = [1]
    index += 1
    submit_receipt(index, cores, start_timestamp, end_timestamp, elapsed_time=1)
    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    start_timestamp = 20
    end_timestamp = 37
    cores = [8]
    index += 1
    submit_receipt(index, cores, start_timestamp, end_timestamp, elapsed_time=1)
    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    start_timestamp = 39
    end_timestamp = 40
    cores = [1]
    index += 1
    submit_receipt(index, cores, start_timestamp, end_timestamp, elapsed_time=1)
    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    start_timestamp = 37
    end_timestamp = 39
    cores = [8]
    index += 1
    submit_receipt(index, cores, start_timestamp, end_timestamp, elapsed_time=1)
    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    start_timestamp = 45
    end_timestamp = 50
    cores = [128]
    index += 1
    submit_receipt(index, cores, start_timestamp, end_timestamp, elapsed_time=1)
    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    start_timestamp = 39
    end_timestamp = 40
    cores = [1]
    index += 1
    submit_receipt(index, cores, start_timestamp, end_timestamp, elapsed_time=1)
    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    start_timestamp = 40
    end_timestamp = 41
    cores = [1]
    index += 1
    submit_receipt(index, cores, start_timestamp, end_timestamp, elapsed_time=1)


def test_test3():
    global provider
    global requester

    provider = accounts[0]
    requester = accounts[1]

    register_provider(100)
    register_requester(requester)

    start_timestamp = 10
    end_timestamp = 20
    cores = [1]
    index = 0
    submit_receipt(index, cores, start_timestamp, end_timestamp, elapsed_time=1)
    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    start_timestamp = 27
    end_timestamp = 35
    cores = [1]
    index = 1
    submit_receipt(index, cores, start_timestamp, end_timestamp, elapsed_time=1)
    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    start_timestamp = 30
    end_timestamp = 45
    cores = [1]
    index = 2
    tx = submit_receipt(index, cores, start_timestamp, end_timestamp, elapsed_time=1)
    gas_base = int(tx.__dict__["gas_used"])
    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    start_timestamp = 34
    end_timestamp = 51
    cores = [1]
    index = 3
    tx = submit_receipt(index, cores, start_timestamp, end_timestamp, elapsed_time=1)
    gas_end = int(tx.__dict__["gas_used"])
    log(f"==> gas_cost_for_iteration={gas_end - gas_base}")
