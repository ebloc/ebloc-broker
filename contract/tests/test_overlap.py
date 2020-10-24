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


@pytest.fixture(scope="module", autouse=True)
def my_own_session_run_at_beginning(_Ebb):
    config.Ebb = _Ebb
    config.w3 = web3


@pytest.fixture(autouse=True)
def run_around_tests():
    new_test()


def check_price_keys(price_keys, provider, source_code_hash1):
    res = config.Ebb.getRegisteredDataBlockNumbers(provider, source_code_hash1)
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


def test_submitJob_gas():
    job = Job()
    provider = accounts[0]
    requester = accounts[1]

    register_provider(100)
    register_requester(requester)

    job.source_code_hashes = [b"8b3e98abb65d0c1aceea8d606fc55403"]
    job.key = job.source_code_hashes[0]
    job.index = 0
    job.cores = [1]
    job.execution_durations = [1]
    job.dataTransferIns = [1]
    job.dataTransferOut = 1
    job.storage_ids = [StorageID.EUDAT.value]
    job.cache_types = [CacheType.PUBLIC.value]
    job.storage_hours = [0]
    job.data_prices_set_block_numbers = [0]

    job_price, _cost = cost(provider, requester, job, config.Ebb, web3)
    provider_price_block_number = config.Ebb.getProviderSetBlockNumbers(provider)[-1]

    args = [
        provider,
        provider_price_block_number,
        job.storage_ids,
        job.cache_types,
        job.data_prices_set_block_numbers,
        job.cores,
        job.execution_durations,
        job.dataTransferOut,
    ]
    tx = config.Ebb.submitJob(
        job.key,
        job.dataTransferIns,
        args,
        job.storage_hours,
        job.source_code_hashes,
        {"from": requester, "value": web3.toWei(job_price, "wei")},
    )

    jobID = 0
    startTime = 10
    tx = config.Ebb.setJobStatusRunning(job.key, job.index, jobID, startTime, {"from": provider})
    rpc.sleep(60)
    mine(5)
    completionTime = 20
    dataTransferIn = 0
    dataTransferOut = 0
    execution_time_min = 1
    args = [job.index, jobID, completionTime, dataTransferIn, dataTransferOut, job.cores, [1], True]

    tx = config.Ebb.processPayment(job.key, args, execution_time_min, "", {"from": provider})
    print("received_gas_used=" + str(tx.__dict__['gas_used']))
    received_sum = tx.events["LogProcessPayment"]["receivedWei"]
    refunded_sum = tx.events["LogProcessPayment"]["refundedWei"]
    # withdraw(provider, received_sum)
    # withdraw(requester, refunded_sum)
    print(config.Ebb.getJobInfo(provider, job.key, job.index, jobID))

    # tx = config.Ebb.processPayment(job.key, args, execution_time_min, zero_bytes32, {"from": provider})
    # ------------
    job = Job()
    job.source_code_hashes = [b"8b3e98abb65d0c1aceea8d606fc55403"]
    job.key = job.source_code_hashes[0]
    job.index = 1
    job.cores = [1]
    job.execution_durations = [1]
    job.dataTransferIns = [1]
    job.dataTransferOut = 1
    job.storage_ids = [StorageID.EUDAT.value]
    job.cache_types = [CacheType.PUBLIC.value]
    job.storage_hours = [0]
    job.data_prices_set_block_numbers = [0]

    job_price, _cost = cost(provider, requester, job, config.Ebb, web3)
    provider_price_block_number = config.Ebb.getProviderSetBlockNumbers(provider)[-1]

    args = [
        provider,
        provider_price_block_number,
        job.storage_ids,
        job.cache_types,
        job.data_prices_set_block_numbers,
        job.cores,
        job.execution_durations,
        job.dataTransferOut,
    ]
    tx = config.Ebb.submitJob(
        job.key,
        job.dataTransferIns,
        args,
        job.storage_hours,
        job.source_code_hashes,
        {"from": requester, "value": web3.toWei(job_price, "wei")},
    )

    jobID = 0
    startTime = 27
    tx = config.Ebb.setJobStatusRunning(job.key, job.index, jobID, startTime, {"from": provider})
    rpc.sleep(60)
    mine(5)

    completionTime = 35
    dataTransferIn = 0
    dataTransferOut = 0
    args = [job.index, jobID, completionTime, dataTransferIn, dataTransferOut, job.cores, [1], True]
    execution_time_min = 1

    tx = config.Ebb.processPayment(job.key, args, execution_time_min, "", {"from": provider})
    print("received_gas_used=" + str(tx.__dict__['gas_used']))
    received_sum = tx.events["LogProcessPayment"]["receivedWei"]
    refunded_sum = tx.events["LogProcessPayment"]["refundedWei"]
    # withdraw(provider, received_sum)
    # withdraw(requester, refunded_sum)
    print(config.Ebb.getJobInfo(provider, job.key, job.index, jobID))

    job = Job()
    job.source_code_hashes = [b"8b3e98abb65d0c1aceea8d606fc55403"]
    job.key = job.source_code_hashes[0]
    job.index = 2
    job.cores = [1]
    job.execution_durations = [1]
    job.dataTransferIns = [1]
    job.dataTransferOut = 1
    job.storage_ids = [StorageID.EUDAT.value]
    job.cache_types = [CacheType.PUBLIC.value]
    job.storage_hours = [0]
    job.data_prices_set_block_numbers = [0]

    job_price, _cost = cost(provider, requester, job, config.Ebb, web3)
    provider_price_block_number = config.Ebb.getProviderSetBlockNumbers(provider)[-1]

    args = [
        provider,
        provider_price_block_number,
        job.storage_ids,
        job.cache_types,
        job.data_prices_set_block_numbers,
        job.cores,
        job.execution_durations,
        job.dataTransferOut,
    ]
    tx = config.Ebb.submitJob(
        job.key,
        job.dataTransferIns,
        args,
        job.storage_hours,
        job.source_code_hashes,
        {"from": requester, "value": web3.toWei(job_price, "wei")},
    )

    jobID = 0
    startTime = 30
    tx = config.Ebb.setJobStatusRunning(job.key, job.index, jobID, startTime, {"from": provider})
    rpc.sleep(60)
    mine(5)
    completionTime = 45
    dataTransferIn = 0
    dataTransferOut = 0
    args = [job.index, jobID, completionTime, dataTransferIn, dataTransferOut, job.cores, [1], True]
    execution_time_min = 1

    tx = config.Ebb.processPayment(job.key, args, execution_time_min, "", {"from": provider})
    gas_base = int(tx.__dict__['gas_used'])
    print("received_gas_used=" + str(tx.__dict__['gas_used']))
    received_sum = tx.events["LogProcessPayment"]["receivedWei"]
    refunded_sum = tx.events["LogProcessPayment"]["refundedWei"]
    # withdraw(provider, received_sum)
    # withdraw(requester, refunded_sum)
    print(config.Ebb.getJobInfo(provider, job.key, job.index, jobID))

    # ------------
    job = Job()
    job.source_code_hashes = [b"8b3e98abb65d0c1aceea8d606fc55403"]

    job.key = job.source_code_hashes[0]
    job.index = 3
    job.cores = [2]
    job.execution_durations = [1]
    job.dataTransferIns = [1]
    job.dataTransferOut = 1
    job.storage_ids = [StorageID.EUDAT.value]
    job.cache_types = [CacheType.PUBLIC.value]
    job.storage_hours = [0]
    job.data_prices_set_block_numbers = [0]

    job_price, _cost = cost(provider, requester, job, config.Ebb, web3)
    provider_price_block_number = config.Ebb.getProviderSetBlockNumbers(provider)[-1]

    args = [
        provider,
        provider_price_block_number,
        job.storage_ids,
        job.cache_types,
        job.data_prices_set_block_numbers,
        job.cores,
        job.execution_durations,
        job.dataTransferOut,
    ]
    tx = config.Ebb.submitJob(
        job.key,
        job.dataTransferIns,
        args,
        job.storage_hours,
        job.source_code_hashes,
        {"from": requester, "value": web3.toWei(job_price, "wei")},
    )
    #
    jobID = 0
    startTime = 34
    # startTime = 44
    tx = config.Ebb.setJobStatusRunning(job.key, job.index, jobID, startTime, {"from": provider})
    rpc.sleep(60)
    mine(5)
    completionTime = 51
    dataTransferIn = 0
    dataTransferOut = 0
    execution_time_min = 1
    args = [job.index, jobID, completionTime, dataTransferIn, dataTransferOut, job.cores, [1], True]

    tx = config.Ebb.processPayment(job.key, args, execution_time_min, "", {"from": provider})
    gas_end = int(tx.__dict__['gas_used'])
    print("received_gas_used=" + str(tx.__dict__['gas_used']))
    received_sum = tx.events["LogProcessPayment"]["receivedWei"]
    refunded_sum = tx.events["LogProcessPayment"]["refundedWei"]
    # withdraw(provider, received_sum)
    # withdraw(requester, refunded_sum)
    print(config.Ebb.getJobInfo(provider, job.key, job.index, jobID))

    size = config.Ebb.getProviderReceiptSize(provider)
    for idx in range(0, size):
        print(config.Ebb.getProviderReceiptNode(provider, idx))

    print("=> gas_cost_for_iteration=" + str(gas_end - gas_base))
