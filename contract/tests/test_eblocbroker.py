#!/usr/bin/python3

import os
import sys
from os import path

import pytest

import brownie
import config
import eblocbroker.Contract as Contract
from brownie import accounts, rpc, web3
from config import setup_logger
from contract.scripts.lib import DataStorage, Job, cost, new_test

# from imports import connect
from utils import CacheType, StorageID, ipfs_to_bytes32, logging, zero_bytes32

# from brownie.test import given, strategy
setup_logger("", True)
config.logging.propagate = False

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

whisper_pub_key = "04aec8867369cd4b38ce7c212a6de9b3aceac4303d05e54d0da5991194c1e28d36361e4859b64eaad1f95951d2168e53d46f3620b1d4d2913dbf306437c62683a6"
cwd = os.getcwd()

provider_email = "provider_test@gmail.com"
federation_cloud_id = "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu"

available_core_num = 128
price_core_min = 1
price_data_transfer = 1
price_storage = 1
price_cache = 1
prices = [price_core_min, price_data_transfer, price_storage, price_cache]
commitmentBlockNum = 240

GPG_FINGERPRINT = "0359190A05DF2B72729344221D522F92EFA2F330"
ipfs_address = "/ip4/79.123.177.145/tcp/4001/ipfs/QmWmZQnb8xh3gHf9ZFmVQC4mLEav3Uht5kHJxZtixG3rsf"
Ebb = None


@pytest.fixture(scope="module", autouse=True)
def my_own_session_run_at_beginning(_Ebb):
    global Ebb
    # connect()
    config.ebb = _Ebb
    config.Ebb = Ebb = Contract.eblocbroker


@pytest.fixture(autouse=True)
def run_around_tests():
    new_test()


def check_price_keys(price_keys, provider, source_code_hash1):
    res = Ebb.getRegisteredDataBlockNumbers(provider, source_code_hash1)
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


def remove_zeros_gpg_fingerprint(_gpg_fingerprint):
    return str(_gpg_fingerprint).replace("0x000000000000000000000000", "").upper()


def get_block_number():
    print(f"block_number={web3.eth.blockNumber} | block_number on contractTx={web3.eth.blockNumber + 1}")
    return web3.eth.blockNumber


def withdraw(address, amount):
    temp = address.balance()
    assert Ebb.balanceOf(address) == amount
    Ebb.withdraw({"from": address, "gas_price": 0})
    received = address.balance() - temp
    assert amount == received
    assert Ebb.balanceOf(address) == 0


def get_block_timestamp():
    return web3.eth.getBlock(get_block_number()).timestamp


def register_provider(price_core_min=1):
    """Register Provider"""
    mine(1)
    web3.eth.defaultAccount = accounts[0]
    prices = [price_core_min, price_data_transfer, price_storage, price_cache]
    tx = config.ebb.registerProvider(
        GPG_FINGERPRINT,
        provider_email,
        federation_cloud_id,
        ipfs_address,
        whisper_pub_key,
        available_core_num,
        prices,
        commitmentBlockNum,
        {"from": accounts[0]},
    )
    provider_registered_bn = tx.block_number
    print(f"Block number when the provider is registered={provider_registered_bn}")
    gpg_fingerprint = remove_zeros_gpg_fingerprint(tx.events["LogProviderInfo"]["gpgFingerprint"])
    assert gpg_fingerprint == GPG_FINGERPRINT
    logging.info(f"gpg_fingerprint={gpg_fingerprint}")

    orc_id = "0000-0001-7642-0442"
    orc_id_as_bytes = str.encode(orc_id)
    assert not config.ebb.isOrcIDVerified(accounts[0]), "orc_id initial value should be false"
    config.ebb.authenticateOrcID(accounts[0], orc_id_as_bytes, {"from": accounts[0]})
    assert config.ebb.isOrcIDVerified(accounts[0]), "isOrcIDVerified is failed"

    # orc_id should only set once for the same user
    with brownie.reverts():
        config.ebb.authenticateOrcID(accounts[0], orc_id_as_bytes, {"from": accounts[0]})

    *_, b = config.ebb.getRequesterInfo(accounts[0])
    assert orc_id == b.decode("utf-8").replace("\x00", ""), "orc_id set false"
    return provider_registered_bn


def register_requester(account):
    """Register requester."""
    tx = config.ebb.registerRequester(
        GPG_FINGERPRINT,
        "alper.alimoglu@gmail.com",
        "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu",
        "/ip4/79.123.177.145/tcp/4001/ipfs/QmWmZQnb8xh3gHf9ZFmVQC4mLEav3Uht5kHJxZtixG3rsf",
        whisper_pub_key,
        {"from": account},
    )
    assert config.ebb.doesRequesterExist(account), True
    gpg_fingerprint = remove_zeros_gpg_fingerprint(tx.events["LogRequester"]["gpgFingerprint"])
    assert gpg_fingerprint == GPG_FINGERPRINT

    orc_id = "0000-0001-7642-0552"
    orc_id_as_bytes = str.encode(orc_id)

    # logging.info(f"isOrcIDVerified={Ebb.isOrcIDVerified(account)}")

    assert not config.ebb.isOrcIDVerified(account), "orc_id initial value should be false"

    config.ebb.authenticateOrcID(account, orc_id_as_bytes, {"from": accounts[0]})  # ORCID should be registered.

    assert config.ebb.isOrcIDVerified(account), "isOrcIDVerified is failed"
    assert not config.ebb.isOrcIDVerified(accounts[9]), "isOrcIDVerified is failed"

    with brownie.reverts():  # orc_id should only set once for the same user
        config.ebb.authenticateOrcID(account, orc_id_as_bytes, {"from": accounts[0]})

    *_, b = config.ebb.getRequesterInfo(account)
    assert orc_id == b.decode("utf-8").replace("\x00", ""), "orc_id set false"


def test_register(ebb):
    config.ebb = ebb
    register_provider(100)
    requester = accounts[1]
    register_requester(requester)


def test_stored_data_usage():
    job = Job()
    provider = accounts[0]
    requester = accounts[1]
    requester_1 = accounts[2]

    register_provider(100)
    register_requester(requester)
    register_requester(requester_1)

    jobKey = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd"
    job.source_code_hashes.append(ipfs_to_bytes32(jobKey))

    jobKey_2 = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Va"
    job.source_code_hashes.append(ipfs_to_bytes32(jobKey_2))

    job.data_transfer_ins = [1, 1]
    job.dataTransferOut = 1
    # provider's registered data won't be used
    job.storage_hours = [1, 1]
    job.data_prices_set_block_numbers = [0, 0]
    job.cores = [1]
    job.run_time = [5]

    job.provider_price_block_number = Ebb.getProviderSetBlockNumbers(accounts[0])[-1]
    job.storage_ids = [StorageID.GDRIVE.value, StorageID.GDRIVE.value]
    job.cache_types = [CacheType.PUBLIC.value, CacheType.PRIVATE.value]
    args = [
        provider,
        job.provider_price_block_number,
        job.storage_ids,
        job.cache_types,
        job.data_prices_set_block_numbers,
        job.cores,
        job.run_time,
        job.dataTransferOut,
    ]

    job_price, _cost = cost(provider, requester, job)

    # first time job is submitted with the data files
    tx = config.ebb.submitJob(
        jobKey,
        job.data_transfer_ins,
        args,
        job.storage_hours,
        job.source_code_hashes,
        {"from": requester, "value": web3.toWei(job_price, "wei")},
    )

    print(tx.events["LogDataStorageRequest"]["owner"])

    print("jobIndex=" + str(tx.events["LogJob"]["index"]))
    print(tx.events["LogJob"]["jobKey"])
    assert _cost["storage"] == 2

    job_price, _cost = cost(provider, requester, job)

    print("jobIndex=" + str(tx.events["LogJob"]["index"]))
    print(tx.events["LogJob"]["jobKey"])
    assert _cost["storage"] == 0, "Since it is not verified yet cost of storage should be 2"
    assert _cost["data_transfer"] == 1

    with brownie.reverts():
        job_price_revert = 500  # dataTransferIn cost is ignored
        tx = Ebb.submitJob(
            jobKey,
            job.data_transfer_ins,
            args,
            job.storage_hours,
            job.source_code_hashes,
            {"from": requester, "value": web3.toWei(job_price_revert, "wei")},
        )

    tx = Ebb.submitJob(
        jobKey,
        job.data_transfer_ins,
        args,
        job.storage_hours,
        job.source_code_hashes,
        {"from": requester, "value": web3.toWei(job_price, "wei")},
    )

    assert "LogDataStorageRequest" not in tx.events
    mine(240)

    job_price, _cost = cost(provider, requester, job)
    # first time job is submitted with the data files
    tx = Ebb.submitJob(
        jobKey,
        job.data_transfer_ins,
        args,
        job.storage_hours,
        job.source_code_hashes,
        {"from": requester, "value": web3.toWei(job_price, "wei")},
    )

    print(tx.events["LogDataStorageRequest"]["owner"])


# @pytest.mark.skip(reason="skip")
def test_ownership():
    """Get Owner"""
    assert Ebb.getOwner() == accounts[0]

    with brownie.reverts():  # transferOwnership should revert
        Ebb.transferOwnership("0x0000000000000000000000000000000000000000", {"from": accounts[0]})

    Ebb.transferOwnership(accounts[1], {"from": accounts[0]})
    assert Ebb.getOwner() == accounts[1]


def test_initial_balances():
    assert Ebb.balanceOf(accounts[0]) == 0


def test_computational_refund():
    job = Job()
    provider = accounts[0]
    requester = accounts[1]

    register_provider(100)
    register_requester(requester)

    job.source_code_hashes = [b"9b3e9babb65d9c1aceea8d606fc55403", b"9a4c0c1c9aadb203daf9367bd4df930b"]
    job.cores = [1]
    job.run_time = [5]
    job.data_transfer_ins = [1, 1]
    job.dataTransferOut = 1
    job.storage_ids = [StorageID.EUDAT.value, StorageID.EUDAT.value]
    job.cache_types = [CacheType.PUBLIC.value, CacheType.PUBLIC.value]
    job.storage_hours = [0, 0]
    job.data_prices_set_block_numbers = [0, 0]

    job_price, _cost = cost(provider, requester, job)

    provider_price_block_number = Ebb.getProviderSetBlockNumbers(accounts[0])[-1]
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
    tx = Ebb.submitJob(
        job.source_code_hashes[0],
        job.data_transfer_ins,
        args,
        job.storage_hours,
        job.source_code_hashes,
        {"from": requester, "value": web3.toWei(job_price, "wei")},
    )

    index = 0
    jobID = 0
    startTime = 1579524978
    tx = Ebb.setJobStatusRunning(job.source_code_hashes[0], index, jobID, startTime, {"from": accounts[0]})
    rpc.sleep(60)
    mine(5)

    args = [index, jobID, 1579524998, 2, 0, job.cores, [5], True]
    run_time = 1
    tx = Ebb.processPayment(job.source_code_hashes[0], args, run_time, zero_bytes32, {"from": accounts[0]})
    received_sum = tx.events["LogProcessPayment"]["receivedWei"]
    refunded_sum = tx.events["LogProcessPayment"]["refundedWei"]
    print(str(received_sum) + " " + str(refunded_sum))
    assert received_sum + refunded_sum == 505
    assert received_sum == 104 and refunded_sum == 401
    withdraw(accounts[0], received_sum)
    withdraw(requester, refunded_sum)


def test_storage_refund():
    job = Job()
    provider = accounts[0]
    requester = accounts[1]

    register_provider()
    register_requester(requester)

    jobKey = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd"
    job.source_code_hashes.append(ipfs_to_bytes32(jobKey))
    job.storage_hours.append(1)

    jobKey_2 = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581V"
    job.source_code_hashes.append(ipfs_to_bytes32(jobKey_2))
    job.storage_hours.append(1)

    job.data_transfer_ins = [100, 100]
    job.dataTransferOut = 100
    job.data_prices_set_block_numbers = [0, 0]

    job.cores = [2]
    job.run_time = [10]

    job.provider_price_block_number = Ebb.getProviderSetBlockNumbers(accounts[0])[-1]
    job.storage_ids = [StorageID.EUDAT.value, StorageID.IPFS.value]
    job.cache_types = [CacheType.PRIVATE.value, CacheType.PUBLIC.value]

    # provider's registered data won't be used
    job.data_prices_set_block_numbers = [0, 0]

    job_price, _cost = cost(provider, requester, job)
    job_price += 1  # for test 1 wei extra is paid
    args = [
        provider,
        job.provider_price_block_number,
        job.storage_ids,
        job.cache_types,
        job.data_prices_set_block_numbers,
        job.cores,
        job.run_time,
        job.dataTransferOut,
    ]
    tx = Ebb.submitJob(
        jobKey,
        job.data_transfer_ins,
        args,
        job.storage_hours,
        job.source_code_hashes,
        {"from": requester, "value": web3.toWei(job_price, "wei")},
    )

    refunded = tx.events["LogJob"]["refunded"]
    print("jobIndex=" + str(tx.events["LogJob"]["index"]))
    print("refunded=" + str(refunded))
    print(tx.events["LogJob"]["jobKey"])
    withdraw(requester, refunded)  # check for extra payment is checked

    index = 0
    jobID = 0
    tx = Ebb.refund(provider, jobKey, index, jobID, job.cores, job.run_time, {"from": provider})
    print(Ebb.getJobInfo(provider, jobKey, index, jobID))
    refundedWei = tx.events["LogRefundRequest"]["refundedWei"]
    print(f"refundedWei={refundedWei}")
    withdraw(requester, refundedWei)

    # VM Exception while processing transaction: invalid opcode
    with brownie.reverts():
        Ebb.getJobInfo(provider, jobKey, 5, jobID)

    storage_cost_sum = 0
    for source_code_hash in job.source_code_hashes:
        storage_cost_sum += Ebb.getReceivedStorageDeposit(provider, requester, source_code_hash)

    assert _cost["storage"] == storage_cost_sum
    assert _cost["computational"] + _cost["data_transfer"] + _cost["cache"] == refundedWei
    mine(240)

    tx = Ebb.refundStorageDeposit(provider, requester, job.source_code_hashes[0], {"from": requester, "gas": 4500000})
    refundedWei = tx.events["LogStorageDeposit"]["payment"]
    print("refundedWei=" + str(refundedWei))
    withdraw(requester, refundedWei)

    with brownie.reverts():  # refundStorageDeposit should revert
        tx = Ebb.refundStorageDeposit(
            provider, requester, job.source_code_hashes[0], {"from": requester, "gas": 4500000}
        )

    tx = Ebb.refundStorageDeposit(provider, requester, job.source_code_hashes[1], {"from": requester, "gas": 4500000})
    refundedWei = tx.events["LogStorageDeposit"]["payment"]
    paid_address = tx.events["LogStorageDeposit"]["paidAddress"]
    withdraw(requester, refundedWei)

    with brownie.reverts():  # refundStorageDeposit should revert
        tx = Ebb.refundStorageDeposit(
            provider, requester, job.source_code_hashes[0], {"from": requester, "gas": 4500000}
        )

    assert requester == paid_address
    assert Ebb.balanceOf(provider) == 0

    print("========= Same Job submitted after full refund =========")
    tx = Ebb.submitJob(
        jobKey,
        job.data_transfer_ins,
        args,
        job.storage_hours,
        job.source_code_hashes,
        {"from": requester, "value": web3.toWei(job_price, "wei")},
    )

    print(f"jobIndex={tx.events['LogJob']['index']}")
    print(tx.events["LogJob"]["jobKey"])

    index = 1
    jobID = 0
    tx = Ebb.refund(provider, jobKey, index, jobID, job.cores, job.run_time, {"from": provider})
    print(Ebb.getJobInfo(provider, jobKey, index, jobID))
    refundedWei = tx.events["LogRefundRequest"]["refundedWei"]
    print("refundedWei=" + str(refundedWei))

    assert _cost["computational"] + _cost["data_transfer"] + _cost["cache"] == refundedWei

    storage_cost_sum = 0
    storage_payment = []
    for source_code_hash in job.source_code_hashes:
        storage_payment.append(Ebb.getReceivedStorageDeposit(provider, requester, source_code_hash))

    job.isVerified = [True, True]
    # called by the cluster
    Ebb.sourceCodeHashReceived(
        jobKey, index, job.source_code_hashes, job.cache_types, job.isVerified, {"from": provider, "gas": 4500000}
    )

    for source_code_hash in job.source_code_hashes:
        print(Ebb.getJobStorageTime(provider, source_code_hash))

    with brownie.reverts():  # refundStorageDeposit should revert, because it is already used by the provider
        for source_code_hash in job.source_code_hashes:
            tx = Ebb.refundStorageDeposit(provider, requester, source_code_hash, {"from": requester, "gas": 4500000})

    with brownie.reverts():
        tx = Ebb.receiveStorageDeposit(requester, job.source_code_hashes[0], {"from": provider, "gas": 4500000})

    mine(240)
    # after deadline (1 hr) is completed to store the data, provider could obtain the money
    for idx, source_code_hash in enumerate(job.source_code_hashes):
        tx = Ebb.receiveStorageDeposit(requester, source_code_hash, {"from": provider, "gas": 4500000})
        amount = tx.events["LogStorageDeposit"]["payment"]
        withdraw(provider, amount)
        assert storage_payment[idx] == amount


def test_update_provider():
    mine(5)
    provider_registered_bn = register_provider()

    federation_cloud_id = "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu"
    Ebb.updateProviderInfo(
        GPG_FINGERPRINT, provider_email, federation_cloud_id, ipfs_address, whisper_pub_key, {"from": accounts[0]}
    )
    print(Ebb.getUpdatedProviderPricesBlocks(accounts[0]))

    available_core_num = 64
    Ebb.updateProviderPrices(available_core_num, commitmentBlockNum, prices, {"from": accounts[0]})

    available_core_num = 128
    Ebb.updateProviderPrices(available_core_num, commitmentBlockNum, prices, {"from": accounts[0]})

    prices_set_block_number = Ebb.getUpdatedProviderPricesBlocks(accounts[0])[1]
    assert Ebb.getProviderInfo(accounts[0], prices_set_block_number)[1][0] == 128

    available_core_num = 16
    Ebb.updateProviderPrices(available_core_num, commitmentBlockNum, prices, {"from": accounts[0]})

    prices_set_block_number = Ebb.getUpdatedProviderPricesBlocks(accounts[0])[1]
    assert Ebb.getProviderInfo(accounts[0], prices_set_block_number)[1][0] == 16
    mine(240)

    available_core_num = 32
    Ebb.updateProviderPrices(available_core_num, commitmentBlockNum, prices, {"from": accounts[0]})

    print(Ebb.getUpdatedProviderPricesBlocks(accounts[0]))
    assert Ebb.getUpdatedProviderPricesBlocks(accounts[0])[2] == commitmentBlockNum * 2 + provider_registered_bn

    providerPriceInfo = Ebb.getProviderInfo(accounts[0], 0)

    block_read_from = providerPriceInfo[0]
    assert block_read_from == commitmentBlockNum + provider_registered_bn


def test_multiple_data():
    job = Job()
    provider = accounts[0]
    requester = accounts[1]
    requester_1 = accounts[2]

    register_provider()
    register_requester(requester)
    register_requester(requester_1)

    jobKey = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd"
    job.source_code_hashes.append(ipfs_to_bytes32(jobKey))

    jobKey_2 = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Va"
    job.source_code_hashes.append(ipfs_to_bytes32(jobKey_2))

    job.data_transfer_ins = [100, 100]
    job.dataTransferOut = 100
    # provider's registered data won't be used
    job.storage_hours = [1, 1]
    job.data_prices_set_block_numbers = [0, 0]
    job.cores = [2]
    job.run_time = [10]
    provider_price_block_number = Ebb.getProviderSetBlockNumbers(accounts[0])[-1]
    job.storage_ids = [StorageID.EUDAT.value, StorageID.IPFS.value]
    job.cache_types = [CacheType.PRIVATE.value, CacheType.PUBLIC.value]
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

    job_price, _cost = cost(provider, requester, job)

    # first time job is submitted with the data files
    tx = Ebb.submitJob(
        jobKey,
        job.data_transfer_ins,
        args,
        job.storage_hours,
        job.source_code_hashes,
        {"from": requester, "value": web3.toWei(job_price, "wei")},
    )

    print("jobIndex=" + str(tx.events["LogJob"]["index"]))
    print(tx.events["LogJob"]["jobKey"])
    assert _cost["storage"] == 200, "Since it is not verified yet cost of storage should be 200"

    # second time job is wanted to send by the same user  with the same data files
    job_price, _cost = cost(provider, requester, job)
    assert _cost["storage"] == 0, "Since cost of storage is already paid by the user it should be 0"

    # second time job is wanted to send by the differnt user  with the same data files
    job_price, _cost = cost(provider, requester_1, job)
    print(str(_cost))
    assert _cost["storage"] == 200, "Since it is not verified yet cost of storage should be 200"

    # => Cluster verifies the gvien data files for the related job
    index = 0
    isVerified_list = [True, True]
    tx = Ebb.sourceCodeHashReceived(
        jobKey, index, job.source_code_hashes, job.cache_types, isVerified_list, {"from": provider, "gas": 4500000}
    )

    # second time job is wanted to send by the differnt user  with the same data files
    job_price, _cost = cost(provider, requester, job)
    assert _cost["storage"] == 0, "Since it is verified torageCost should be 0"

    # second time job is wanted to send by the differnt user  with the same data files
    job_price, _cost = cost(provider, requester_1, job)
    assert _cost["storage"] == 100, "Since data1 is verified and publis, its cost of storage should be 0"

    # ds = scripts.DataStorage(provider, source_code_hashes[1], True)

    job_price, _cost = cost(provider, requester, job)

    assert _cost["storage"] == 0, "Since it is paid on first job submittion it should be 0"
    assert _cost["data_transfer"] == job.dataTransferOut, "cost of data_transfer should cover only dataTransferOut"
    tx = Ebb.submitJob(
        jobKey,
        job.data_transfer_ins,
        args,
        job.storage_hours,
        job.source_code_hashes,
        {"from": requester, "value": web3.toWei(job_price, "wei")},
    )

    print("job_index=" + str(tx.events["LogJob"]["index"]))

    # provider side:
    index = 0
    jobID = 0
    startTime = get_block_timestamp()
    execution_time = 10
    result_ipfs_hash = "0xabcd"
    tx = Ebb.setJobStatusRunning(jobKey, index, jobID, startTime, {"from": accounts[0]})

    rpc.sleep(15 * 4 * execution_time)
    mine(1)
    end_time = startTime + 15 * 4 * execution_time
    args = [
        index,
        jobID,
        end_time,
        sum(job.data_transfer_ins),
        job.dataTransferOut,
        job.cores,
        job.run_time,
        False,
    ]
    tx = Ebb.processPayment(jobKey, args, execution_time, result_ipfs_hash, {"from": accounts[0]})
    received_sum = tx.events["LogProcessPayment"]["receivedWei"]
    refunded_sum = tx.events["LogProcessPayment"]["refundedWei"]
    print(f"{received_sum} {refunded_sum}")
    assert received_sum == 320 and refunded_sum == 0
    withdraw(accounts[0], received_sum)
    withdraw(requester, refunded_sum)

    dataTransferIn = 0  # already requested on index==0
    dataTransferOut = 100
    dataTransfer = [dataTransferIn, dataTransferOut]

    index = 1
    jobID = 0
    startTime = get_block_timestamp()
    execution_time = 10
    result_ipfs_hash = "0xabcd"
    tx = Ebb.setJobStatusRunning(jobKey, index, jobID, startTime, {"from": accounts[0]})

    rpc.sleep(15 * 4 * execution_time)
    mine(1)
    end_time = startTime + 15 * 4 * execution_time

    args = [index, jobID, end_time, dataTransfer[0], dataTransfer[1], job.cores, job.run_time, False]
    tx = Ebb.processPayment(jobKey, args, execution_time, result_ipfs_hash, {"from": accounts[0]})

    # print(tx.events['LogProcessPayment'])
    received_sum = tx.events["LogProcessPayment"]["receivedWei"]
    refunded_sum = tx.events["LogProcessPayment"]["refundedWei"]
    print(str(received_sum) + " " + str(refunded_sum))
    assert received_sum == 120 and refunded_sum == 0
    withdraw(accounts[0], received_sum)
    withdraw(requester, refunded_sum)


def test_workflow():
    job = Job()
    provider = accounts[0]
    requester = accounts[1]

    register_provider()
    register_requester(requester)

    jobKey = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd"
    source_code_hash = ipfs_to_bytes32(jobKey)
    with brownie.reverts():  # getJobInfo should revert
        Ebb.updataDataPrice(source_code_hash, 20, 100, {"from": provider})

    Ebb.registerData(source_code_hash, 20, 240, {"from": provider})
    Ebb.removeRegisteredData(source_code_hash, {"from": provider})  # should submitJob fail if it is not removed

    source_code_hash1 = "0x68b8d8218e730fc2957bcb12119cb204"
    # "web3.toBytes(hexstr=ipfs_to_bytes32("QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Ve"))
    Ebb.registerData(source_code_hash1, 20, 240, {"from": provider})
    mine(6)

    with brownie.reverts():  # registerData should revert
        Ebb.registerData(source_code_hash1, 20, 1000, {"from": provider})

    Ebb.updataDataPrice(source_code_hash1, 250, 241, {"from": provider})

    data_block_numbers = Ebb.getRegisteredDataBlockNumbers(provider, source_code_hash1)
    print(f"getRegisteredDataBlockNumbers={data_block_numbers[1]}")
    get_block_number()
    data_prices = Ebb.getRegisteredDataPrice(provider, source_code_hash1, 0)
    print(f"registerDataPrice={data_prices}")
    assert data_prices[0] == 20

    res = Ebb.getRegisteredDataPrice(provider, source_code_hash1, data_block_numbers[1])
    print(f"registerDataPrice={res}")
    assert res[0] == 250

    mine(231)

    res = Ebb.getRegisteredDataPrice(provider, source_code_hash1, 0)
    print(f"registerDataPrice={res}")
    assert res[0] == 20
    mine(1)

    res = Ebb.getRegisteredDataPrice(provider, source_code_hash1, 0)
    print(f"registerDataPrice={res}")
    assert res[0] == 250

    job.source_code_hashes = [source_code_hash, source_code_hash1]  # Hashed of the data file in array
    job.storage_hours = [0, 0]

    job.data_transfer_ins = [100, 100]
    job.dataTransferOut = 100

    # job.data_prices_set_block_numbers = [0, 253]  # TODO: check this ex 253 exists or not
    job.data_prices_set_block_numbers = [0, data_block_numbers[1]]  # TODO: check this ex 253 exists or not
    check_price_keys(job.data_prices_set_block_numbers, provider, source_code_hash1)

    job.cores = [2, 4, 2]
    job.run_time = [10, 15, 20]

    job.storage_ids = [StorageID.IPFS.value, StorageID.IPFS.value]
    job.cache_types = [CacheType.PUBLIC.value, CacheType.PUBLIC.value]
    args = [
        provider,
        Ebb.getProviderSetBlockNumbers(accounts[0])[-1],
        job.storage_ids,
        job.cache_types,
        job.data_prices_set_block_numbers,
        job.cores,
        job.run_time,
        job.dataTransferOut,
    ]

    job_price, _cost = cost(provider, requester, job)

    # first submit
    tx = Ebb.submitJob(
        jobKey,
        job.data_transfer_ins,
        args,
        job.storage_hours,
        job.source_code_hashes,
        {"from": requester, "value": web3.toWei(job_price, "wei")},
    )

    print(Ebb.getJobInfo(provider, jobKey, 0, 0))
    print(Ebb.getJobInfo(provider, jobKey, 0, 1))
    print(Ebb.getJobInfo(provider, jobKey, 0, 2))

    print("-------------------")
    assert (
        tx.events["LogRegisteredDataRequestToUse"][0]["registeredDataHash"]
        == "0x0000000000000000000000000000000068b8d8218e730fc2957bcb12119cb204"
    ), "Registered Data should be used"

    with brownie.reverts():  # getJobInfo should revert
        print(Ebb.getJobInfo(provider, jobKey, 1, 2))
        print(Ebb.getJobInfo(provider, jobKey, 0, 3))

    # setJobStatus for the workflow:
    index = 0
    jobID = 0
    startTime = 10
    tx = Ebb.setJobStatusRunning(jobKey, index, jobID, startTime, {"from": accounts[0]})

    index = 0
    jobID = 1
    startTime = 20
    tx = Ebb.setJobStatusRunning(jobKey, index, jobID, startTime, {"from": accounts[0]})

    # processPayment for the workflow:
    index = 0
    jobID = 0
    execution_time = 10
    dataTransfer = [100, 0]
    end_time = 20
    result_ipfs_hash = ipfs_to_bytes32("QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Ve")

    received_sums = []
    refunded_sums = []
    received_sum = 0
    refunded_sum = 0
    args = [index, jobID, end_time, dataTransfer[0], dataTransfer[1], job.cores, job.run_time, False]
    tx = Ebb.processPayment(jobKey, args, execution_time, result_ipfs_hash, {"from": accounts[0]})
    # print(tx.events['LogProcessPayment'])
    received_sums.append(tx.events["LogProcessPayment"]["receivedWei"])
    refunded_sums.append(tx.events["LogProcessPayment"]["refundedWei"])
    received_sum += tx.events["LogProcessPayment"]["receivedWei"]
    refunded_sum += tx.events["LogProcessPayment"]["refundedWei"]
    print(f"received_sum={received_sum} | refunded_sum={refunded_sum} | job_price={job_price}")
    # ------------------
    index = 0
    jobID = 1
    execution_time = 15
    dataTransfer = [0, 0]
    end_time = 39
    result_ipfs_hash = ipfs_to_bytes32("QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Ve")

    args = [index, jobID, end_time, dataTransfer[0], dataTransfer[1], job.cores, job.run_time, False]
    tx = Ebb.processPayment(jobKey, args, execution_time, result_ipfs_hash, {"from": accounts[0]})
    received_sums.append(tx.events["LogProcessPayment"]["receivedWei"])
    refunded_sums.append(tx.events["LogProcessPayment"]["refundedWei"])
    received_sum += tx.events["LogProcessPayment"]["receivedWei"]
    refunded_sum += tx.events["LogProcessPayment"]["refundedWei"]
    print(f"received_sum={received_sum} | refunded_sum={refunded_sum} | job_price={job_price}")

    # --------
    index = 0
    jobID = 2
    execution_time = 20
    dataTransfer = [0, 100]
    end_time = 39
    result_ipfs_hash = ipfs_to_bytes32("QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Ve")

    with brownie.reverts():  # processPayment should revert, setRunning is not called for the job=2
        args = [
            index,
            jobID,
            end_time,
            dataTransfer[0],
            dataTransfer[1],
            job.cores,
            job.run_time,
            False,
        ]
        tx = Ebb.processPayment(jobKey, args, execution_time, result_ipfs_hash, {"from": accounts[0]})

    index = 0
    jobID = 2
    startTime = 20
    tx = Ebb.setJobStatusRunning(jobKey, index, jobID, startTime, {"from": accounts[0]})

    args = [index, jobID, end_time, dataTransfer[0], dataTransfer[1], job.cores, job.run_time, True]
    tx = Ebb.processPayment(jobKey, args, execution_time, result_ipfs_hash, {"from": accounts[0]})

    # print(tx.events['LogProcessPayment'])
    received_sums.append(tx.events["LogProcessPayment"]["receivedWei"])
    refunded_sums.append(tx.events["LogProcessPayment"]["refundedWei"])
    received_sum += tx.events["LogProcessPayment"]["receivedWei"]
    refunded_sum += tx.events["LogProcessPayment"]["refundedWei"]
    print(f"received_sum={received_sum} | refunded_sum={refunded_sum} | job_price={job_price}")
    print(received_sums)
    print(refunded_sums)
    assert job_price - _cost["storage"] == received_sum + refunded_sum
    withdraw(accounts[0], received_sum)
    withdraw(requester, refunded_sum)
    # Ebb.updateDataReceivedBlock(result_ipfs_hash, {"from": accounts[4]})


def test_simple_submit():
    job = Job()
    provider = accounts[0]
    requester = accounts[1]

    price_core_min = 100
    register_provider(price_core_min)
    register_requester(requester)

    job.source_code_hashes = [b"9b3e9babb65d9c1aceea8d606fc55403", b"9a4c0c1c9aadb203daf9367bd4df930b"]
    job.key = job.source_code_hashes[0]
    job.cores = [2]
    job.run_time = [1]
    job.data_transfer_ins = [1, 1]
    job.dataTransferOut = 1
    job.storage_ids = [StorageID.EUDAT.value, StorageID.EUDAT.value]
    job.cache_types = [CacheType.PUBLIC.value, CacheType.PUBLIC.value]
    job.storage_hours = [0, 0]
    job.data_prices_set_block_numbers = [0, 0]

    job_price, _cost = cost(provider, requester, job)
    provider_price_block_number = Ebb.getProviderSetBlockNumbers(accounts[0])[-1]

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

    tx = Ebb.submitJob(
        job.key,
        job.data_transfer_ins,
        args,
        job.storage_hours,
        job.source_code_hashes,
        {"from": requester, "value": web3.toWei(job_price, "wei")},
    )

    print("submitJob_gas_used=" + str(tx.__dict__["gas_used"]))
    index = 0
    jobID = 0
    startTime = 1579524978
    tx = Ebb.setJobStatusRunning(job.key, index, jobID, startTime, {"from": provider})
    rpc.sleep(60)
    mine(5)

    completionTime = 1579524998
    dataTransferIn = 0
    dataTransferOut = 0.01
    args = [index, jobID, completionTime, dataTransferIn, dataTransferOut, job.cores, [1], True]
    elapsed_time = 1
    out_hash = b"[46\x17\x98r\xc2\xfc\xe7\xfc\xb8\xdd\n\xd6\xe8\xc5\xca$fZ\xebVs\xec\xff\x06[\x1e\xd4f\xce\x99"
    tx = Ebb.processPayment(job.key, args, elapsed_time, out_hash, {"from": accounts[0]})
    # tx = Ebb.processPayment(job.source_code_hashes[0], args, elapsed_time, zero_bytes32, {"from": accounts[0]})
    received_sum = tx.events["LogProcessPayment"]["receivedWei"]
    refunded_sum = tx.events["LogProcessPayment"]["refundedWei"]
    # print(str(received_sum) + " " + str(refunded_sum))
    assert received_sum == job.cores[0] * price_core_min and refunded_sum == 5
    withdraw(accounts[0], received_sum)
    withdraw(requester, refunded_sum)


def test_submit_job(ebb):
    breakpoint()  # DEBUG
    job = Job()
    provider = accounts[0]
    requester = accounts[1]

    register_provider()
    register_requester(requester)

    fname = f"{cwd}/files/test.txt"
    # fname = cwd + '/files/test_.txt'

    print("Registered provider addresses:")
    print(Ebb.getProviders())

    providerPriceInfo = Ebb.getProviderInfo(accounts[0], 0)
    # block_read_from = providerPriceInfo[0]
    _providerPriceInfo = providerPriceInfo[1]
    # availableCoreNum = _providerPriceInfo[0]
    # commitmentBlockDuration = _providerPriceInfo[1]
    price_core_min = _providerPriceInfo[2]
    # price_data_transfer = _providerPriceInfo[3]
    # price_storage = _providerPriceInfo[4]
    # price_cache = _providerPriceInfo[5]

    print("Provider's available_core_num=" + str(available_core_num))
    print("Provider's price_core_min=" + str(price_core_min))
    print(providerPriceInfo)

    job_priceSum = 0
    jobID = 0
    index = 0
    with open(fname) as f:
        for line in f:
            arguments = line.rstrip("\n").split(" ")

            storageHour = 1
            coreMin = int(arguments[1]) - int(arguments[0])
            core = int(arguments[2])

            job.cores = [core]
            job.run_time = [coreMin]
            # time.sleep(1)
            # rpc.mine(int(arguments[0]))

            jobKey = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd"  # source Code's jobKey
            dataKey = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd"  # source Code's jobKey
            source_code_hash = ipfs_to_bytes32(dataKey)

            # print("Client Balance before: " + str(web3.eth.balanceOf(account)))
            # print("Contract Balance before: " + str(web3.eth.balanceOf(accounts[0])))

            job.source_code_hashes = [source_code_hash]  # Hashed of the
            job.storage_hours = [storageHour]

            job.data_transfer_ins = [100]
            job.dataTransferOut = 100
            job.data_prices_set_block_numbers = [0]
            job.storage_ids = [StorageID.IPFS.value]
            job.cache_types = [CacheType.PUBLIC.value]

            args = [
                provider,
                Ebb.getProviderSetBlockNumbers(accounts[0])[-1],
                job.storage_ids,
                job.cache_types,
                job.data_prices_set_block_numbers,
                job.cores,
                job.run_time,
                job.dataTransferOut,
            ]

            # print(source_code_hashes[0])
            job_price, _cost = cost(provider, requester, job)

            job_priceSum += job_price
            data_transfer_ins = [100]

            tx = Ebb.submitJob(
                jobKey,
                data_transfer_ins,
                args,
                job.storage_hours,
                job.source_code_hashes,
                {"from": requester, "value": web3.toWei(job_price, "wei")},
            )
            # print('submitJob => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))
            print("job_index=" + str(tx.events["LogJob"]["index"]))

            # print("Contract Balance after: " + str(web3.eth.balanceOf(accouts[0])))
            # print("Client Balance after: " + str(web3.eth.balanceOf(accounts[8])))
            # sys.stdout.write('jobInfo: ')
            # sys.stdout.flush()
            print(Ebb.getJobInfo(provider, jobKey, index, jobID))
            index += 1

    print(f"total_paid={job_priceSum}")
    # print(block_read_from)
    # rpc.mine(100)
    # print(web3.eth.blockNumber)

    jobID = 0
    with open(fname) as f:
        for index, line in enumerate(f):
            arguments = line.rstrip("\n").split(" ")
            tx = Ebb.setJobStatusRunning(jobKey, index, jobID, int(arguments[0]), {"from": accounts[0]})
            if index == 0:
                with brownie.reverts():
                    tx = Ebb.setJobStatusRunning(jobKey, index, jobID, int(arguments[0]) + 1, {"from": accounts[0]})

    print("----------------------------------")
    result_ipfs_hash = ipfs_to_bytes32("QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Ve")
    with open(fname) as f:
        for index, line in enumerate(f):
            arguments = line.rstrip("\n").split(" ")
            if index == 0:
                data_transfer_in_sum = 90
                job.dataTransferOut = 100
            else:
                data_transfer_in_sum = 0
                job.dataTransferOut = 100

            coreMin = int(arguments[1]) - int(arguments[0])
            core = int(arguments[2])

            job.cores = [core]
            job.run_time = [coreMin]

            print("\nContractBalance=" + str(Ebb.getContractBalance()))
            jobID = 0
            execution_time = int(arguments[1]) - int(arguments[0])
            end_time = int(arguments[1])
            args = [
                index,
                jobID,
                end_time,
                data_transfer_in_sum,
                job.dataTransferOut,
                job.cores,
                job.run_time,
                True,
            ]
            tx = Ebb.processPayment(jobKey, args, execution_time, result_ipfs_hash, {"from": accounts[0]})
            # source_code_hashes
            received = tx.events["LogProcessPayment"]["receivedWei"]
            refunded = tx.events["LogProcessPayment"]["refundedWei"]
            withdraw(accounts[0], received)
            withdraw(requester, refunded)
            print(f"received={received} | refunded={refunded}")

    print("\nContractBalance=" + str(Ebb.getContractBalance()))
    # prints finalize version of the linked list.
    size = Ebb.getProviderReceiptSize(provider)
    for idx in range(0, size):
        print(Ebb.getProviderReceiptNode(provider, idx))

    print("----------------------------------")
    print(f"StorageTime for job: {jobKey}")
    ds = DataStorage(Ebb, web3, provider, source_code_hash, True)

    print(
        f"receivedBlockNumber={ds.received_block} |"
        f"storage_duration(block numbers)={ds.storage_duration} | "
        f"is_private={ds.is_private} |"
        f"isVerified_Used={ds.is_verified_used}"
    )
    print(
        "received_storage_deposit="
        + str(Ebb.getReceivedStorageDeposit(provider, requester, source_code_hash, {"from": provider}))
    )
    # print("\x1b[6;30;42m" + "========== DONE ==========" + "\x1b[0m")

    """
    mine(240)
    tx = Ebb.receiveStorageDeposit(requester, source_code_hash, {"from": provider});
    print('receiveStorageDeposit => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))
    print(Ebb.getReceivedStorageDeposit(requester, source_code_hash, {"from": }))
    print('----------------------------------')
    """
