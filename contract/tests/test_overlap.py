#!/usr/bin/env python3

import os
import sys
from os import path

import pytest

import config
from brownie import accounts, rpc, web3
from config import setup_logger
from contract.scripts.lib import Job, cost, new_test
from contract.tests.test_eblocbroker import register_provider, register_requester, withdraw  # noqa
from imports import connect
from utils import CacheType, StorageID

# from brownie.test import given, strategy
setup_logger("", True)
config.logging.propagate = False

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

whisper_pub_key = "04aec8867369cd4b38ce7c212a6de9b3aceac4303d05e54d0da5991194c1e28d36361e4859b64eaad1f95951d2168e53d46f3620b1d4d2913dbf306437c62683a6"
cwd = os.getcwd()

provider_email = "provider@gmail.com"
federatedCloudID = "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu"

available_core_num = 128
price_core_min = 1
price_data_transfer = 1
price_storage = 1
price_cache = 1
prices = [price_core_min, price_data_transfer, price_storage, price_cache]
commitmentBlockNum = 240

GPG_FINGERPRINT = "0359190A05DF2B72729344221D522F92EFA2F330"
ipfs_address = "/ip4/79.123.177.145/tcp/4001/ipfs/QmWmZQnb8xh3gHf9ZFmVQC4mLEav3Uht5kHJxZtixG3rsf"

provider = None
requester = None
ebb = None


@pytest.fixture(scope="module", autouse=True)
def my_own_session_run_at_beginning(_Ebb):
    global ebb
    connect()
    config.ebb = _Ebb
    ebb = _Ebb


@pytest.fixture(autouse=True)
def run_around_tests():
    new_test()


def check_list(is_print=True):
    size = config.ebb.getProviderReceiptSize(provider)
    if is_print:
        print(f"length={size}")

    for idx in range(0, size):
        value = config.ebb.getProviderReceiptNode(provider, idx)
        if is_print:
            print(value)

    _list = []
    carried_sum = 0
    for idx in range(0, size):
        value = config.ebb.getProviderReceiptNode(provider, idx)
        if value[0] != 0:
            carried_sum += value[1]

        assert (
            carried_sum <= available_core_num
        ), f"carried sum={carried_sum} exceed available_core_num={available_core_num}"

        _list.append(value[0])

    assert _list == sorted(_list, reverse=True)
    assert carried_sum == 0


def check_price_keys(price_keys, provider, source_code_hash1):
    res = config.ebb.getRegisteredDataBlockNumbers(provider, source_code_hash1)
    for key in price_keys:
        if key > 0:
            assert key in res, f"{key} does no exist in price keys({res}) for the registered data{source_code_hash1}"


def mine(block_number):
    # https://stackoverflow.com/a/775075/2402577
    m, s = divmod(block_number * 15, 60)
    h, m = divmod(m, 60)
    height = web3.eth.blockNumber
    rpc.mine(block_number)
    print(
        f"Mine {block_number} empty blocks == {h:d}:{m:02d}:{s:02d} (h/m/s) |"
        f" current_block_number={web3.eth.blockNumber}"
    )
    assert web3.eth.blockNumber == height + block_number


def submit_receipt(index, cores, startTime, completionTime, elapsed_time, is_print=True):
    print("==> [" + str(startTime) + ", " + str(completionTime) + "]" + " cores=" + str(cores))
    job = Job()
    job.source_code_hashes = [b"8b3e98abb65d0c1aceea8d606fc55403"]
    job.key = job.source_code_hashes[0]
    job.index = index
    job.cores = cores
    job.run_time = [1]
    job.data_transfer_ins = [1]
    job.dataTransferOut = 1
    job.storage_ids = [StorageID.EUDAT.value]
    job.cache_types = [CacheType.PUBLIC.value]
    job.storage_hours = [0]
    job.data_prices_set_block_numbers = [0]

    job_price, _cost = cost(provider, requester, job)
    provider_price_block_number = config.ebb.getProviderSetBlockNumbers(provider)[-1]

    args = [
        provider,
        provider_price_block_number,
        job.storage_ids,
        job.cache_types,
        job.data_prices_set_block_numbers,
        job.cores,
        job.run_time,
        job.dataTransferOut,
    ]
    tx = config.ebb.submitJob(
        job.key,
        job.data_transfer_ins,
        args,
        job.storage_hours,
        job.source_code_hashes,
        {"from": requester, "value": web3.toWei(job_price, "wei")},
    )

    jobID = 0
    tx = config.ebb.setJobStatusRunning(job.key, job.index, jobID, startTime, {"from": provider})
    rpc.sleep(60)
    mine(5)
    data_transfer_in = 0
    dataTransferOut = 0

    args = [job.index, jobID, completionTime, data_transfer_in, dataTransferOut, job.cores, [1], True]
    tx = config.ebb.processPayment(job.key, args, elapsed_time, "", {"from": provider})
    if is_print:
        print("received_gas_used=" + str(tx.__dict__["gas_used"]))
    # received_sum = tx.events["LogProcessPayment"]["receivedWei"]
    # refunded_sum = tx.events["LogProcessPayment"]["refundedWei"]
    # withdraw(provider, received_sum)
    # withdraw(requester, refunded_sum)
    check_list(is_print)
    if is_print:
        print("==============================================")
    return tx


def test_submitJob_gas():
    global provider
    global requester

    provider = accounts[0]
    requester = accounts[1]

    register_provider(100)
    register_requester(requester)

    startTime = 10
    completionTime = 20
    cores = [127]
    index = 0
    submit_receipt(index, cores, startTime, completionTime, elapsed_time=1)
    # -------------------
    startTime = 10
    completionTime = 25
    cores = [1]
    index = 1
    submit_receipt(index, cores, startTime, completionTime, elapsed_time=1)
    # -------------------
    startTime = 11
    completionTime = 25
    cores = [1]
    index = 2
    tx = submit_receipt(index, cores, startTime, completionTime, elapsed_time=1)
    gas_base = int(tx.__dict__["gas_used"])
    # -------------------
    startTime = 8
    completionTime = 9
    cores = [65]
    index = 3
    tx = submit_receipt(index, cores, startTime, completionTime, elapsed_time=1)
    gas_end = int(tx.__dict__["gas_used"])
    check_list()
    print("==> gas_cost_for_iteration=" + str(gas_end - gas_base))
    # TODO: : revert on tx check


def test_test1():
    global provider
    global requester

    provider = accounts[0]
    requester = accounts[1]

    register_provider(100)
    register_requester(requester)

    startTime = 10
    completionTime = 20
    cores = [1]
    index = 0
    submit_receipt(index, cores, startTime, completionTime, elapsed_time=1)
    # -------------------
    startTime = 27
    completionTime = 35
    cores = [1]
    index = 1
    submit_receipt(index, cores, startTime, completionTime, elapsed_time=1)
    # -------------------
    startTime = 30
    completionTime = 45
    cores = [1]
    index = 2
    submit_receipt(index, cores, startTime, completionTime, elapsed_time=1)
    # -------------------
    startTime = 30
    completionTime = 45
    cores = [1]
    index = 3
    submit_receipt(index, cores, startTime, completionTime, elapsed_time=1)
    # -------------------
    startTime = 27
    completionTime = 30
    cores = [120]
    index = 4
    submit_receipt(index, cores, startTime, completionTime, elapsed_time=1)


def test_test2():
    global provider
    global requester

    provider = accounts[0]
    requester = accounts[1]

    register_provider(100)
    register_requester(requester)

    startTime = 10
    completionTime = 20
    cores = [1]
    index = 0
    submit_receipt(index, cores, startTime, completionTime, elapsed_time=1)
    # -------------------
    startTime = 10
    completionTime = 20
    cores = [128]
    index += 1
    submit_receipt(index, cores, startTime, completionTime, elapsed_time=1)
    # -------------------
    startTime = 9
    completionTime = 19
    cores = [128]
    index += 1
    submit_receipt(index, cores, startTime, completionTime, elapsed_time=1)
    # -------------------
    startTime = 11
    completionTime = 21
    cores = [128]
    index += 1
    submit_receipt(index, cores, startTime, completionTime, elapsed_time=1)
    # -------------------
    startTime = 15
    completionTime = 25
    cores = [1]
    index += 1
    submit_receipt(index, cores, startTime, completionTime, elapsed_time=1)
    # -------------------
    startTime = 8
    completionTime = 9
    cores = [1]
    index += 1
    submit_receipt(index, cores, startTime, completionTime, elapsed_time=1)
    # -------------------
    startTime = 40
    completionTime = 45
    cores = [1]
    index += 1
    submit_receipt(index, cores, startTime, completionTime, elapsed_time=1)
    # -------------------
    startTime = 40
    completionTime = 45
    cores = [126]
    index += 1
    submit_receipt(index, cores, startTime, completionTime, elapsed_time=1)
    # -------------------
    startTime = 41
    completionTime = 45
    cores = [1]
    index += 1
    submit_receipt(index, cores, startTime, completionTime, elapsed_time=1)
    # -------------------
    startTime = 39
    completionTime = 41
    cores = [1]
    index += 1
    submit_receipt(index, cores, startTime, completionTime, elapsed_time=1)
    # -------------------
    startTime = 26
    completionTime = 39
    cores = [1]
    index += 1
    submit_receipt(index, cores, startTime, completionTime, elapsed_time=1)
    # -------------------
    startTime = 20
    completionTime = 38
    cores = [1]
    index += 1
    submit_receipt(index, cores, startTime, completionTime, elapsed_time=1)
    # -------------------
    startTime = 20
    completionTime = 37
    cores = [8]
    index += 1
    submit_receipt(index, cores, startTime, completionTime, elapsed_time=1)
    # -------------------
    startTime = 39
    completionTime = 40
    cores = [1]
    index += 1
    submit_receipt(index, cores, startTime, completionTime, elapsed_time=1)
    # -------------------
    startTime = 37
    completionTime = 39
    cores = [8]
    index += 1
    submit_receipt(index, cores, startTime, completionTime, elapsed_time=1)
    # -------------------
    startTime = 45
    completionTime = 50
    cores = [128]
    index += 1
    submit_receipt(index, cores, startTime, completionTime, elapsed_time=1)
    # -------------------
    startTime = 39
    completionTime = 40
    cores = [1]
    index += 1
    submit_receipt(index, cores, startTime, completionTime, elapsed_time=1)
    # -------------------
    startTime = 40
    completionTime = 41
    cores = [1]
    index += 1
    submit_receipt(index, cores, startTime, completionTime, elapsed_time=1)


def test_test3():
    global provider
    global requester

    provider = accounts[0]
    requester = accounts[1]

    register_provider(100)
    register_requester(requester)

    startTime = 10
    completionTime = 20
    cores = [1]
    index = 0
    submit_receipt(index, cores, startTime, completionTime, elapsed_time=1)
    # -------------------
    startTime = 27
    completionTime = 35
    cores = [1]
    index = 1
    submit_receipt(index, cores, startTime, completionTime, elapsed_time=1)
    # -------------------
    startTime = 30
    completionTime = 45
    cores = [1]
    index = 2
    tx = submit_receipt(index, cores, startTime, completionTime, elapsed_time=1)
    gas_base = int(tx.__dict__["gas_used"])
    # -------------------
    startTime = 34
    completionTime = 51
    cores = [1]
    index = 3
    tx = submit_receipt(index, cores, startTime, completionTime, elapsed_time=1)
    gas_end = int(tx.__dict__["gas_used"])
    print("==> gas_cost_for_iteration=" + str(gas_end - gas_base))
