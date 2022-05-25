#!/usr/bin/python3

import os
import sys
from os import path

import pytest

import brownie
from broker import cfg, config
from broker._utils._log import console_ruler
from broker.config import setup_logger
from broker.eblocbroker_scripts import Contract
from broker.eblocbroker_scripts.job import DataStorage, Job
from broker.utils import CacheType, StorageID, ipfs_to_bytes32, log, zero_bytes32
from brownie import accounts, rpc, web3
from brownie.network.state import Chain
from contract.scripts.lib import mine, new_test

COMMITMENT_BLOCK_NUM = 600
Contract.eblocbroker = Contract.Contract(is_brownie=True)

# from brownie.test import given, strategy
setup_logger("", True)
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
cwd = os.getcwd()
provider_gmail = "provider_test@gmail.com"
fid = "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu"

available_core = 128
price_core_min = 1
price_data_transfer = 1
price_storage = 1
price_cache = 1
prices = [price_core_min, price_data_transfer, price_storage, price_cache]

GPG_FINGERPRINT = "0359190A05DF2B72729344221D522F92EFA2F330"
ipfs_address = "/ip4/79.123.177.145/tcp/4001/ipfs/QmWmZQnb8xh3gHf9ZFmVQC4mLEav3Uht5kHJxZtixG3rsf"
Ebb = None
chain = None
ebb = None

gas_costs = {}
gas_costs["registerRequester"] = []
gas_costs["registerProvider"] = []
gas_costs["setJobStateRunning"] = []
gas_costs["refund"] = []
gas_costs["setDataVerified"] = []
gas_costs["processPayment"] = []
gas_costs["withdraw"] = []
gas_costs["authenticateOrcID"] = []
gas_costs["depositStorage"] = []
gas_costs["updateProviderInfo"] = []
gas_costs["updataDataPrice"] = []
gas_costs["updateProviderPrices"] = []
gas_costs["registerData"] = []


def to_gwei(value):
    return web3.toWei(value, "gwei")


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
    log(f"block_number={web3.eth.blockNumber} | contract_bn={web3.eth.blockNumber + 1}", "bold")
    return web3.eth.blockNumber


def get_block_timestamp():
    return web3.eth.getBlock(get_block_number()).timestamp


def withdraw(address, amount):
    temp = address.balance()
    assert ebb.balanceOf(address) == amount
    tx = ebb.withdraw({"from": address, "gas_price": 0})
    gas_costs["withdraw"].append(tx.__dict__["gas_used"])
    received = address.balance() - temp
    assert to_gwei(amount) == received
    assert ebb.balanceOf(address) == 0


def register_provider(price_core_min=1):
    """Register Provider"""
    ebb = config.ebb
    mine(1)
    web3.eth.defaultAccount = accounts[0]
    prices = [price_core_min, price_data_transfer, price_storage, price_cache]
    tx = config.ebb.registerProvider(
        GPG_FINGERPRINT,
        provider_gmail,
        fid,
        ipfs_address,
        available_core,
        prices,
        COMMITMENT_BLOCK_NUM,
        {"from": accounts[0]},
    )
    gas_costs["registerProvider"].append(tx.__dict__["gas_used"])
    provider_registered_bn = tx.block_number
    log(f"block number when the provider is registered={provider_registered_bn}", "bold")
    gpg_fingerprint = remove_zeros_gpg_fingerprint(tx.events["LogProviderInfo"]["gpgFingerprint"])
    assert gpg_fingerprint == GPG_FINGERPRINT
    log(f"==> gpg_fingerprint={gpg_fingerprint}")
    orc_id = "0000-0001-7642-0442"
    orc_id_as_bytes = str.encode(orc_id)
    assert not ebb.isOrcIDVerified(accounts[0]), "orc_id initial value should be false"
    tx = ebb.authenticateOrcID(accounts[0], orc_id_as_bytes, {"from": accounts[0]})
    gas_costs["authenticateOrcID"].append(tx.__dict__["gas_used"])
    assert ebb.isOrcIDVerified(accounts[0]), "isOrcIDVerified() is failed"
    # orc_id should only set once for the same user
    with brownie.reverts():
        tx = ebb.authenticateOrcID(accounts[0], orc_id_as_bytes, {"from": accounts[0]})

    assert orc_id == ebb.getOrcID(accounts[0]).decode("utf-8").replace("\x00", ""), "orc_id set false"
    return provider_registered_bn


def register_requester(account):
    """Register requester."""
    ebb = config.ebb
    tx = ebb.registerRequester(
        GPG_FINGERPRINT,
        "alper.alimoglu@gmail.com",
        "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu",
        "/ip4/79.123.177.145/tcp/4001/ipfs/QmWmZQnb8xh3gHf9ZFmVQC4mLEav3Uht5kHJxZtixG3rsf",
        {"from": account},
    )
    gas_costs["registerRequester"].append(tx.__dict__["gas_used"])
    assert ebb.doesRequesterExist(account), True
    gpg_fingerprint = remove_zeros_gpg_fingerprint(tx.events["LogRequester"]["gpgFingerprint"])
    assert gpg_fingerprint == GPG_FINGERPRINT

    orc_id = "0000-0001-7642-0552"
    orc_id_as_bytes = str.encode(orc_id)
    assert not ebb.isOrcIDVerified(account), "orc_id initial value should be false"

    tx = ebb.authenticateOrcID(account, orc_id_as_bytes, {"from": accounts[0]})  # ORCID should be registered.
    assert ebb.isOrcIDVerified(account), "isOrcIDVerified is failed"
    assert not ebb.isOrcIDVerified(accounts[9]), "isOrcIDVerified is failed"
    with brownie.reverts():  # orc_id should only set once for the same user
        ebb.authenticateOrcID(account, orc_id_as_bytes, {"from": accounts[0]})

    assert orc_id == ebb.getOrcID(account).decode("utf-8").replace("\x00", ""), "orc_id set false"


def test_register():
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
    job_key = "1v12W1CJwSKE-SPFiq86pGpF74WPNRBD2"
    job.code_hashes.append(b"050e6cc8dd7e889bf7874689f1e1ead6")
    job.code_hashes.append(b"b6aaf03752dc68d625fc57b451faa2bf")
    job.data_transfer_ins = [1, 1]
    job.data_transfer_out = 1
    # provider's registered data won't be used
    job.storage_hours = [1, 1]
    job.data_prices_set_block_numbers = [0, 0]
    job.cores = [1]
    job.run_time = [5]
    job.provider_price_block_number = ebb.getProviderSetBlockNumbers(accounts[0])[-1]
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
        job.data_transfer_out,
    ]
    job_price, cost = job.cost(provider, requester)
    # first time job is submitted with the data files
    # https://stackoverflow.com/a/12468284/2402577
    tx = ebb.submitJob(
        job_key,
        job.data_transfer_ins,
        args,
        job.storage_hours,
        job.code_hashes,
        {"from": requester, "value": to_gwei(job_price)},
    )
    log(tx.events["LogDataStorageRequest"]["owner"])
    key = tx.events["LogJob"]["jobKey"]
    assert tx.events["LogJob"]["received"] == 505
    log(f"==> job_index={tx.events['LogJob']['index']} | key={key}")
    assert cost["storage"] == 2
    job_price, cost = job.cost(provider, requester)
    log(f"==> key={tx.events['LogJob']['jobKey']} | job_index={tx.events['LogJob']['index']}")
    assert cost["storage"] == 0, "Since it is not verified yet cost of storage should be 2"
    assert cost["data_transfer"] == 1
    with brownie.reverts():
        job_price_revert = 500  # data_transfer_in cost is ignored
        tx = ebb.submitJob(
            job.code_hashes[0],
            job.data_transfer_ins,
            args,
            job.storage_hours,
            job.code_hashes,
            {"from": requester, "value": to_gwei(job_price_revert)},
        )
        # log(dict(tx.events["LogJob"]))
        # log(tx.events["LogJob"]["received"] - tx.events["LogJob"]["refunded"])

    tx = ebb.submitJob(
        job.code_hashes[0],
        job.data_transfer_ins,
        args,
        job.storage_hours,
        job.code_hashes,
        {"from": requester, "value": to_gwei(job_price)},
    )
    assert "LogDataStorageRequest" not in tx.events
    mine(cfg.ONE_HOUR_BLOCK_DURATION)
    job_price, cost = job.cost(provider, requester)
    # first time job is submitted with the data files
    tx = ebb.submitJob(
        job.code_hashes[0],
        job.data_transfer_ins,
        args,
        job.storage_hours,
        job.code_hashes,
        {"from": requester, "value": to_gwei(job_price)},
    )
    log(tx.events["LogDataStorageRequest"]["owner"])


# @pytest.mark.skip(reason="skip")
def test_ownership():
    """Get Owner"""
    assert ebb.getOwner() == accounts[0]

    with brownie.reverts():
        ebb.transferOwnership(cfg.ZERO_ADDRESS, {"from": accounts[0]})

    ebb.transferOwnership(accounts[1], {"from": accounts[0]})
    assert ebb.getOwner() == accounts[1]


def test_initial_balances():
    assert ebb.balanceOf(accounts[0]) == 0


def test_data_info():
    job = Job()
    provider = accounts[0]
    requester = accounts[1]
    register_provider(100)
    register_requester(requester)
    job_key = b"9b3e9babb65d9c1aceea8d606fc55403"
    job.code_hashes = [job_key, b"9a4c0c1c9aadb203daf9367bd4df930b"]
    job.cores = [1]
    job.run_time = [5]
    job.data_transfer_ins = [0, 1]
    job.data_transfer_out = 1
    job.storage_ids = [StorageID.IPFS.value, StorageID.IPFS.value]
    job.cache_types = [CacheType.PUBLIC.value, CacheType.PUBLIC.value]
    job.storage_hours = [0, 1]
    job.data_prices_set_block_numbers = [0, 0]
    job_price, *_ = job.cost(provider, requester)
    provider_price_block_number = ebb.getProviderSetBlockNumbers(accounts[0])[-1]
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
    ebb.submitJob(
        job_key,
        job.data_transfer_ins,
        args,
        job.storage_hours,
        job.code_hashes,
        {"from": requester, "value": to_gwei(job_price)},
    )
    provider_price_info = ebb.getProviderInfo(provider, 0)
    price_cache = provider_price_info[1][4]
    storage_payment = []
    for idx, code_hash in enumerate(job.code_hashes):
        deposit, *_ = ebb.getStorageInfo(provider, requester, code_hash)
        storage_payment.append(deposit)
        assert storage_payment[idx] == job.storage_hours[idx] * price_cache

    job.is_verified = [False, True]
    tx = ebb.setDataVerified([job.code_hashes[1]], {"from": provider, "gas": 4500000})
    for idx, code_hash in enumerate(job.code_hashes):
        *_, output = ebb.getStorageInfo(provider, cfg.ZERO_ADDRESS, code_hash)
        assert output[3] == job.is_verified[idx]
        # requester is data_owner

    for idx, code_hash in enumerate(job.code_hashes):
        with brownie.reverts():
            tx = ebb.depositStorage(requester, code_hash, {"from": provider, "gas": 4500000})
            gas_costs["depositStorage"].append(tx.__dict__["gas_used"])

    mine(cfg.ONE_HOUR_BLOCK_DURATION)
    for idx, code_hash in enumerate(job.code_hashes):
        *_, output = ebb.getStorageInfo(provider, cfg.ZERO_ADDRESS, code_hash)
        if output[3]:
            tx = ebb.depositStorage(requester, code_hash, {"from": provider, "gas": 4500000})
            gas_costs["depositStorage"].append(tx.__dict__["gas_used"])
            print(tx.events["LogDepositStorage"])


def test_computational_refund():
    job = Job()
    provider = accounts[0]
    requester = accounts[1]
    register_provider(100)
    register_requester(requester)
    job.code_hashes = [b"9b3e9babb65d9c1aceea8d606fc55403", b"9a4c0c1c9aadb203daf9367bd4df930b"]
    job.cores = [1]
    job.run_time = [5]
    job.data_transfer_ins = [1, 1]
    job.data_transfer_out = 1
    job.storage_ids = [StorageID.EUDAT.value, StorageID.EUDAT.value]
    job.cache_types = [CacheType.PUBLIC.value, CacheType.PUBLIC.value]
    job.storage_hours = [0, 0]
    job.data_prices_set_block_numbers = [0, 0]
    job_price, *_ = job.cost(provider, requester)
    provider_price_block_number = ebb.getProviderSetBlockNumbers(accounts[0])[-1]
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
        job.code_hashes[0],
        job.data_transfer_ins,
        args,
        job.storage_hours,
        job.code_hashes,
        {"from": requester, "value": to_gwei(job_price)},
    )
    index = 0
    job_id = 0
    start_timestamp = 1579524978
    tx = ebb.setJobStateRunning(job.code_hashes[0], index, job_id, start_timestamp, {"from": accounts[0]})
    gas_costs["setJobStateRunning"].append(tx.__dict__["gas_used"])
    rpc.sleep(60)
    mine(5)
    run_time = 1
    args = [index, job_id, 1579524998, 2, 0, run_time, job.cores, [5], True]
    tx = ebb.processPayment(job.code_hashes[0], args, zero_bytes32, {"from": accounts[0]})
    received_sum = tx.events["LogProcessPayment"]["receivedGwei"]
    refunded_sum = tx.events["LogProcessPayment"]["refundedGwei"]
    assert tx.events["LogProcessPayment"]["elapsedTime"] == run_time
    log(f"{received_sum} {refunded_sum}")
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
    job_key = "QmQv4AAL8DZNxZeK3jfJGJi63v1msLMZGan7vSsCDXzZud"
    job.code_hashes.append(ipfs_to_bytes32(job_key))
    job.storage_hours.append(1)
    job.code_hashes.append(ipfs_to_bytes32("QmVqtWxuBdZQdLnLce6XCBMuqoazAcbmuxoJHQbfbuqDu2"))
    job.storage_hours.append(1)
    job.data_transfer_ins = [100, 100]
    job.data_transfer_out = 100
    job.data_prices_set_block_numbers = [0, 0]
    job.cores = [2]
    job.run_time = [10]
    job.provider_price_block_number = ebb.getProviderSetBlockNumbers(accounts[0])[-1]
    job.storage_ids = [StorageID.EUDAT.value, StorageID.IPFS.value]
    job.cache_types = [CacheType.PRIVATE.value, CacheType.PUBLIC.value]
    job.data_prices_set_block_numbers = [0, 0]  # provider's registered data won't be used
    job_price, cost = job.cost(provider, requester)
    job_price += 1  # for test additional 1 Gwei is paid
    args = [
        provider,
        job.provider_price_block_number,
        job.storage_ids,
        job.cache_types,
        job.data_prices_set_block_numbers,
        job.cores,
        job.run_time,
        job.data_transfer_out,
    ]
    tx = ebb.submitJob(
        job_key,
        job.data_transfer_ins,
        args,
        job.storage_hours,
        job.code_hashes,
        {"from": requester, "value": to_gwei(job_price)},
    )

    refunded = tx.events["LogJob"]["refunded"]
    log(f"==> job_index={tx.events['LogJob']['index']}")
    log(f"refunded={refunded}", "bold")
    log(f"==> key={tx.events['LogJob']['jobKey']} | job_index={tx.events['LogJob']['index']}")
    assert requester == tx.events["LogJob"]["owner"]
    withdraw(requester, refunded)  # check for extra payment is checked
    index = 0
    job_id = 0
    tx = ebb.refund(provider, job_key, index, job_id, job.cores, job.run_time, {"from": provider})
    gas_costs["refund"].append(tx.__dict__["gas_used"])
    log(ebb.getJobInfo(provider, job_key, index, job_id))
    refunded_gwei = tx.events["LogRefundRequest"]["refundedGwei"]
    log(f"refunded_gwei={refunded_gwei}", "bold")
    withdraw(requester, refunded_gwei)
    # VM Exception while processing transaction: invalid opcode
    with brownie.reverts():
        ebb.getJobInfo(provider, job_key, 5, job_id)

    storage_cost_sum = 0
    for code_hash in job.code_hashes:
        _storage_cost_sum, *_ = ebb.getStorageInfo(provider, requester, code_hash)
        storage_cost_sum += _storage_cost_sum

    assert cost["storage"] == storage_cost_sum
    assert cost["computational"] + cost["data_transfer"] + cost["cache"] == refunded_gwei
    mine(cfg.ONE_HOUR_BLOCK_DURATION)
    tx = ebb.refundStorageDeposit(provider, requester, job.code_hashes[0], {"from": requester, "gas": 4500000})
    refunded_gwei = tx.events["LogDepositStorage"]["payment"]
    log(f"refunded_gwei={refunded_gwei}", "bold")
    withdraw(requester, refunded_gwei)
    with brownie.reverts():
        tx = ebb.refundStorageDeposit(provider, requester, job.code_hashes[0], {"from": requester, "gas": 4500000})

    tx = ebb.refundStorageDeposit(provider, requester, job.code_hashes[1], {"from": requester, "gas": 4500000})
    refunded_gwei = tx.events["LogDepositStorage"]["payment"]
    paid_address = tx.events["LogDepositStorage"]["paidAddress"]
    withdraw(requester, refunded_gwei)
    with brownie.reverts():
        tx = ebb.refundStorageDeposit(provider, requester, job.code_hashes[0], {"from": requester, "gas": 4500000})

    assert requester == paid_address
    assert ebb.balanceOf(provider) == 0
    console_ruler("same job submitted after full refund", color="blue")
    tx = ebb.submitJob(
        job_key,
        job.data_transfer_ins,
        args,
        job.storage_hours,
        job.code_hashes,
        {"from": requester, "value": to_gwei(job_price)},
    )
    log(f"==> key={tx.events['LogJob']['jobKey']} | job_index={tx.events['LogJob']['index']}")
    index = 1
    job_id = 0
    tx = ebb.refund(provider, job_key, index, job_id, job.cores, job.run_time, {"from": provider})
    gas_costs["refund"].append(tx.__dict__["gas_used"])
    log(ebb.getJobInfo(provider, job_key, index, job_id))
    refunded_gwei = tx.events["LogRefundRequest"]["refundedGwei"]
    log(f"refunded_gwei={refunded_gwei}", "bold")
    assert cost["computational"] + cost["data_transfer"] + cost["cache"] == refunded_gwei
    storage_cost_sum = 0
    storage_payment = []
    for code_hash in job.code_hashes:
        deposit, *_ = ebb.getStorageInfo(provider, requester, code_hash)
        storage_payment.append(deposit)

    job.is_verified = [True, True]
    tx = ebb.setDataVerified(job.code_hashes, {"from": provider, "gas": 4500000})
    gas_costs["setDataVerified"].append(tx.__dict__["gas_used"])
    # ebb.dataReceived(  # called by the provider
    #     job_key, index, job.code_hashes, job.cache_types, job.is_verified, {"from": provider, "gas": 4500000}
    # )
    for code_hash in job.code_hashes:
        *_, output = ebb.getStorageInfo(provider, cfg.ZERO_ADDRESS, code_hash)
        log(output, "bold")

    with brownie.reverts():  # refundStorageDeposit should revert, because it is already used by the provider
        for code_hash in job.code_hashes:
            tx = ebb.refundStorageDeposit(provider, requester, code_hash, {"from": requester, "gas": 4500000})
            gas_costs["depositStorage"].append(tx.__dict__["gas_used"])

        tx = ebb.depositStorage(requester, job.code_hashes[0], {"from": provider, "gas": 4500000})
        gas_costs["depositStorage"].append(tx.__dict__["gas_used"])

    mine(cfg.ONE_HOUR_BLOCK_DURATION)
    # after deadline (1 hr) is completed to store the data, provider could obtain the money
    for idx, code_hash in enumerate(job.code_hashes):
        tx = ebb.depositStorage(requester, code_hash, {"from": provider, "gas": 4500000})
        gas_costs["depositStorage"].append(tx.__dict__["gas_used"])
        amount = tx.events["LogDepositStorage"]["payment"]
        withdraw(provider, amount)
        assert storage_payment[idx] == amount


def test_update_provider():
    mine(5)
    provider_registered_bn = register_provider()
    fid = "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu"
    tx = ebb.updateProviderInfo(GPG_FINGERPRINT, provider_gmail, fid, ipfs_address, {"from": accounts[0]})
    gas_costs["updateProviderInfo"].append(tx.__dict__["gas_used"])
    log(ebb.getUpdatedProviderPricesBlocks(accounts[0]))
    available_core = 64
    prices = [2, 2, 2, 2]
    tx = ebb.updateProviderPrices(available_core, COMMITMENT_BLOCK_NUM, prices, {"from": accounts[0]})
    gas_costs["updateProviderPrices"].append(tx.__dict__["gas_used"])

    prices = [3, 3, 3, 3]  # update prices right away to check overwrite
    tx = ebb.updateProviderPrices(available_core, COMMITMENT_BLOCK_NUM, prices, {"from": accounts[0]})
    gas_costs["updateProviderPrices"].append(tx.__dict__["gas_used"])

    prices = [4, 4, 4, 4]  # update prices right away to check overwrite
    tx = ebb.updateProviderPrices(available_core, COMMITMENT_BLOCK_NUM, prices, {"from": accounts[0]})
    gas_costs["updateProviderPrices"].append(tx.__dict__["gas_used"])

    prices_set_block_number = ebb.getUpdatedProviderPricesBlocks(accounts[0])
    provider_info = ebb.getProviderInfo(accounts[0], prices_set_block_number[-1])
    assert 4 == provider_info[1][2] == provider_info[1][3] == provider_info[1][4] == provider_info[1][5]
    provider_info = ebb.getProviderInfo(accounts[0], prices_set_block_number[0])
    assert 1 == provider_info[1][2] == provider_info[1][3] == provider_info[1][4] == provider_info[1][5]

    available_core = 128
    tx = ebb.updateProviderPrices(available_core, COMMITMENT_BLOCK_NUM, prices, {"from": accounts[0]})
    gas_costs["updateProviderPrices"].append(tx.__dict__["gas_used"])

    prices_set_block_number = ebb.getUpdatedProviderPricesBlocks(accounts[0])[1]
    assert ebb.getProviderInfo(accounts[0], prices_set_block_number)[1][0] == 128

    available_core = 16
    tx = ebb.updateProviderPrices(available_core, COMMITMENT_BLOCK_NUM, prices, {"from": accounts[0]})
    gas_costs["updateProviderPrices"].append(tx.__dict__["gas_used"])

    prices_set_block_number = ebb.getUpdatedProviderPricesBlocks(accounts[0])[1]
    assert ebb.getProviderInfo(accounts[0], prices_set_block_number)[1][0] == 16
    mine(cfg.ONE_HOUR_BLOCK_DURATION)

    available_core = 32
    tx = ebb.updateProviderPrices(available_core, COMMITMENT_BLOCK_NUM, prices, {"from": accounts[0]})
    gas_costs["updateProviderPrices"].append(tx.__dict__["gas_used"])

    log(ebb.getUpdatedProviderPricesBlocks(accounts[0]))
    assert ebb.getUpdatedProviderPricesBlocks(accounts[0])[2] == COMMITMENT_BLOCK_NUM * 2 + provider_registered_bn

    provider_price_info = ebb.getProviderInfo(accounts[0], 0)
    block_read_from = provider_price_info[0]
    assert block_read_from == COMMITMENT_BLOCK_NUM + provider_registered_bn


def test_multiple_data():
    job = Job()
    provider = accounts[0]
    requester = accounts[1]
    requester_1 = accounts[2]
    register_provider()
    register_requester(requester)
    register_requester(requester_1)
    job_key = "QmQv4AAL8DZNxZeK3jfJGJi63v1msLMZGan7vSsCDXzZud"
    job.code_hashes.append(ipfs_to_bytes32(job_key))
    job.code_hashes.append(ipfs_to_bytes32("QmVqtWxuBdZQdLnLce6XCBMuqoazAcbmuxoJHQbfbuqDu2"))

    job.data_transfer_ins = [100, 100]
    job.data_transfer_out = 100
    # provider's registered data won't be used
    job.storage_hours = [1, 1]
    job.data_prices_set_block_numbers = [0, 0]
    job.cores = [2]
    job.run_time = [10]
    provider_price_block_number = ebb.getProviderSetBlockNumbers(accounts[0])[-1]
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
        job.data_transfer_out,
    ]

    job_price, cost = job.cost(provider, requester)
    # first time job is submitted with the data files
    tx = ebb.submitJob(
        job_key,
        job.data_transfer_ins,
        args,
        job.storage_hours,
        job.code_hashes,
        {"from": requester, "value": to_gwei(job_price)},
    )
    log(f"==> key={tx.events['LogJob']['jobKey']} | job_index={tx.events['LogJob']['index']}")
    assert cost["storage"] == 200, "Since it is not verified yet cost of storage should be 200"

    # second time job is wanted to send by the same user  with the same data files
    job_price, cost = job.cost(provider, requester)
    assert cost["storage"] == 0, "Since cost of storage is already paid by the user it should be 0"

    # second time job is wanted to send by the differnt user  with the same data files
    job_price, cost = job.cost(provider, requester_1)
    log(f"==> cost={cost}")
    assert cost["storage"] == 200, "Since it is not verified yet cost of storage should be 200"
    # cluster verifies the given data files for the related job
    index = 0
    # is_verified_list = [True, True]
    tx = ebb.setDataVerified(job.code_hashes, {"from": provider, "gas": 4500000})
    gas_costs["setDataVerified"].append(tx.__dict__["gas_used"])
    tx = ebb.setDataPublic(
        job_key,
        index,
        job.code_hashes,
        job.cache_types,
        {"from": provider, "gas": 4500000},
    )
    #: second time job is wanted to send by the differnt user  with the same data files
    job_price, cost = job.cost(provider, requester)
    assert cost["storage"] == 0, "Since it is verified storageCost should be 0"
    #: second time job is wanted to send by the differnt user  with the same data files
    job_price, cost = job.cost(provider, requester_1)
    assert cost["storage"] == 100, "Since data1 is verified and public, its cost of storage should be 0"
    # ds = scripts.DataStorage(provider, code_hashes[1], True)
    job_price, cost = job.cost(provider, requester)
    assert cost["storage"] == 0, "Since it is paid on first job submittion it should be 0"
    assert cost["data_transfer"] == job.data_transfer_out, "cost of data_transfer should cover only data_transfer_out"
    tx = ebb.submitJob(
        job_key,
        job.data_transfer_ins,
        args,
        job.storage_hours,
        job.code_hashes,
        {"from": requester, "value": to_gwei(job_price)},
    )
    log(f"job_index={tx.events['LogJob']['index']}", "bold")
    # ===== provider side =====
    index = 0
    job_id = 0
    elapsed_time = 10
    result_ipfs_hash = "0xabcd"
    start_timestamp = get_block_timestamp()
    tx = ebb.setJobStateRunning(job_key, index, job_id, start_timestamp, {"from": accounts[0]})
    gas_costs["setJobStateRunning"].append(tx.__dict__["gas_used"])
    mine(60 * elapsed_time / cfg.BLOCK_DURATION + 1)
    ended_timestamp = start_timestamp + 60 * elapsed_time
    block_timestamp = get_block_timestamp()
    assert (
        ended_timestamp <= block_timestamp
    ), f"block timestamp is ahead of timestamp of when the job ended, difference={block_timestamp - ended_timestamp}"
    args = [
        index,
        job_id,
        ended_timestamp,
        sum(job.data_transfer_ins),
        job.data_transfer_out,
        elapsed_time,
        job.cores,
        job.run_time,
        False,
    ]
    tx = ebb.processPayment(job_key, args, result_ipfs_hash, {"from": accounts[0]})
    assert tx.events["LogProcessPayment"]["elapsedTime"] == elapsed_time
    received_sum = tx.events["LogProcessPayment"]["receivedGwei"]
    refunded_sum = tx.events["LogProcessPayment"]["refundedGwei"]
    log(f"received_sum={received_sum} refunded_sum={refunded_sum}", "bold")
    assert received_sum == 320 and refunded_sum == 0
    withdraw(accounts[0], received_sum)
    withdraw(requester, refunded_sum)
    data_transfer_in = 0  # already requested on index==0
    data_transfer_out = 100
    data_transfer = [data_transfer_in, data_transfer_out]
    index = 1
    job_id = 0
    start_timestamp = get_block_timestamp()
    elapsed_time = 10
    result_ipfs_hash = "0xabcd"
    tx = ebb.setJobStateRunning(job_key, index, job_id, start_timestamp, {"from": accounts[0]})
    gas_costs["setJobStateRunning"].append(tx.__dict__["gas_used"])
    mine(60 * elapsed_time / cfg.BLOCK_DURATION)
    ended_timestamp = start_timestamp + 60 * elapsed_time
    args = [
        index,
        job_id,
        ended_timestamp,
        data_transfer[0],
        data_transfer[1],
        elapsed_time,
        job.cores,
        job.run_time,
        False,
    ]
    tx = ebb.processPayment(job_key, args, result_ipfs_hash, {"from": accounts[0]})
    assert tx.events["LogProcessPayment"]["elapsedTime"] == elapsed_time
    gas_costs["processPayment"].append(tx.__dict__["gas_used"])
    # log(tx.events['LogProcessPayment'])
    received_sum = tx.events["LogProcessPayment"]["receivedGwei"]
    refunded_sum = tx.events["LogProcessPayment"]["refundedGwei"]
    log(f"received_sum={received_sum} refunded_sum={refunded_sum}", "bold")
    assert received_sum == 120 and refunded_sum == 0
    withdraw(accounts[0], received_sum)
    withdraw(requester, refunded_sum)


def test_workflow():
    job = Job()
    provider = accounts[0]
    requester = accounts[1]
    register_provider()
    register_requester(requester)
    job_key = "QmQv4AAL8DZNxZeK3jfJGJi63v1msLMZGan7vSsCDXzZud"
    code_hash = ipfs_to_bytes32(job_key)
    with brownie.reverts():
        ebb.updataDataPrice(code_hash, 20, 100, {"from": provider})

    tx = ebb.registerData(code_hash, 20, cfg.ONE_HOUR_BLOCK_DURATION, {"from": provider})
    gas_costs["registerData"].append(tx.__dict__["gas_used"])

    ebb.removeRegisteredData(code_hash, {"from": provider})  # should submitJob fail if it is not removed
    code_hash1 = "0x68b8d8218e730fc2957bcb12119cb204"
    ebb.registerData(code_hash1, 20, cfg.ONE_HOUR_BLOCK_DURATION, {"from": provider})
    gas_costs["registerData"].append(tx.__dict__["gas_used"])
    mine(6)
    with brownie.reverts():
        ebb.registerData(code_hash1, 21, 1000, {"from": provider})

    tx = ebb.updataDataPrice(code_hash1, 250, cfg.ONE_HOUR_BLOCK_DURATION, {"from": provider})
    gas_costs["updataDataPrice"].append(tx.__dict__["gas_used"])
    tx = ebb.updataDataPrice(code_hash1, 251, cfg.ONE_HOUR_BLOCK_DURATION + 1, {"from": provider})
    gas_costs["updataDataPrice"].append(tx.__dict__["gas_used"])
    data_block_numbers = ebb.getRegisteredDataBlockNumbers(provider, code_hash1)
    log(f"get_registered_data_block_numbers={data_block_numbers[1]}", "bold")
    get_block_number()
    data_prices = ebb.getRegisteredDataPrice(provider, code_hash1, 0)
    assert data_prices[0] == 20
    output = ebb.getRegisteredDataPrice(provider, code_hash1, data_block_numbers[-1])
    assert output[0] == 251
    mine(cfg.ONE_HOUR_BLOCK_DURATION - 10)
    output = ebb.getRegisteredDataPrice(provider, code_hash1, 0)
    log(f"register_data_price={output}", "bold")
    assert output[0] == 20
    mine(1)
    output = ebb.getRegisteredDataPrice(provider, code_hash1, 0)
    log(f"register_data_price={output}", "bold")
    assert output[0] == 251

    job.code_hashes = [code_hash, code_hash1]  # Hashed of the data file in array
    job.storage_hours = [0, 0]
    job.data_transfer_ins = [100, 0]
    job.data_transfer_out = 100

    # job.data_prices_set_block_numbers = [0, 253]  # TODO: check this ex 253 exists or not
    job.data_prices_set_block_numbers = [0, data_block_numbers[1]]  # TODO: check this ex 253 exists or not
    check_price_keys(job.data_prices_set_block_numbers, provider, code_hash1)
    job.cores = [2, 4, 2]
    job.run_time = [10, 15, 20]
    job.storage_ids = [StorageID.IPFS.value, StorageID.NONE.value]
    job.cache_types = [CacheType.PUBLIC.value, CacheType.PUBLIC.value]
    args = [
        provider,
        ebb.getProviderSetBlockNumbers(accounts[0])[-1],
        job.storage_ids,
        job.cache_types,
        job.data_prices_set_block_numbers,
        job.cores,
        job.run_time,
        job.data_transfer_out,
    ]

    job_price, cost = job.cost(provider, requester)
    tx = ebb.submitJob(  # first submit
        job_key,
        job.data_transfer_ins,
        args,
        job.storage_hours,
        job.code_hashes,
        {"from": requester, "value": to_gwei(job_price)},
    )
    for idx in range(0, 3):
        log(ebb.getJobInfo(provider, job_key, 0, idx))

    console_ruler(character="-=")
    assert (
        tx.events["LogRegisteredDataRequestToUse"][0]["registeredDataHash"]
        == "0x0000000000000000000000000000000068b8d8218e730fc2957bcb12119cb204"
    ), "registered data should be used"

    with brownie.reverts():
        log(ebb.getJobInfo(provider, job_key, 1, 2))
        log(ebb.getJobInfo(provider, job_key, 0, 3))

    # setJobState for the workflow:
    index = 0
    job_id = 0
    start_timestamp = 10
    tx = ebb.setJobStateRunning(job_key, index, job_id, start_timestamp, {"from": accounts[0]})
    gas_costs["setJobStateRunning"].append(tx.__dict__["gas_used"])
    index = 0
    job_id = 1
    start_timestamp = 20
    tx = ebb.setJobStateRunning(job_key, index, job_id, start_timestamp, {"from": accounts[0]})
    gas_costs["setJobStateRunning"].append(tx.__dict__["gas_used"])
    # process_payment for the workflow
    index = 0
    job_id = 0
    elapsed_time = 10
    data_transfer = [100, 0]
    ended_timestamp = 20
    result_ipfs_hash = ipfs_to_bytes32("QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Ve")
    received_sums = []
    refunded_sums = []
    received_sum = 0
    refunded_sum = 0
    args = [
        index,
        job_id,
        ended_timestamp,
        data_transfer[0],
        data_transfer[1],
        elapsed_time,
        job.cores,
        job.run_time,
        False,
    ]
    tx = ebb.processPayment(job_key, args, result_ipfs_hash, {"from": accounts[0]})
    gas_costs["processPayment"].append(tx.__dict__["gas_used"])
    # log(tx.events['LogProcessPayment'])
    received_sums.append(tx.events["LogProcessPayment"]["receivedGwei"])
    refunded_sums.append(tx.events["LogProcessPayment"]["refundedGwei"])
    received_sum += tx.events["LogProcessPayment"]["receivedGwei"]
    refunded_sum += tx.events["LogProcessPayment"]["refundedGwei"]
    log(f"received_sum={received_sum} | refunded_sum={refunded_sum} | job_price={job_price}", "bold")
    index = 0
    job_id = 1
    elapsed_time = 15
    data_transfer = [0, 0]
    ended_timestamp = 39
    result_ipfs_hash = ipfs_to_bytes32("QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Ve")
    args = [
        index,
        job_id,
        ended_timestamp,
        data_transfer[0],
        data_transfer[1],
        elapsed_time,
        job.cores,
        job.run_time,
        False,
    ]
    tx = ebb.processPayment(job_key, args, result_ipfs_hash, {"from": accounts[0]})
    assert tx.events["LogProcessPayment"]["elapsedTime"] == elapsed_time
    gas_costs["processPayment"].append(tx.__dict__["gas_used"])
    received_sums.append(tx.events["LogProcessPayment"]["receivedGwei"])
    refunded_sums.append(tx.events["LogProcessPayment"]["refundedGwei"])
    received_sum += tx.events["LogProcessPayment"]["receivedGwei"]
    refunded_sum += tx.events["LogProcessPayment"]["refundedGwei"]
    log(f"received_sum={received_sum} | refunded_sum={refunded_sum} | job_price={job_price}", "bold")
    index = 0
    job_id = 2
    elapsed_time = 20
    data_transfer = [0, 100]
    ended_timestamp = 39
    result_ipfs_hash = ipfs_to_bytes32("QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Ve")
    with brownie.reverts():  # processPayment should revert, setRunning is not called for the job=2
        args = [
            index,
            job_id,
            ended_timestamp,
            data_transfer[0],
            data_transfer[1],
            elapsed_time,
            job.cores,
            job.run_time,
            False,
        ]
        tx = ebb.processPayment(job_key, args, result_ipfs_hash, {"from": accounts[0]})
        gas_costs["processPayment"].append(tx.__dict__["gas_used"])

    index = 0
    job_id = 2
    start_timestamp = 20
    tx = ebb.setJobStateRunning(job_key, index, job_id, start_timestamp, {"from": accounts[0]})
    gas_costs["setJobStateRunning"].append(tx.__dict__["gas_used"])
    args = [
        index,
        job_id,
        ended_timestamp,
        data_transfer[0],
        data_transfer[1],
        elapsed_time,
        job.cores,
        job.run_time,
        True,
    ]
    tx = ebb.processPayment(job_key, args, result_ipfs_hash, {"from": accounts[0]})
    assert tx.events["LogProcessPayment"]["elapsedTime"] == elapsed_time
    gas_costs["processPayment"].append(tx.__dict__["gas_used"])
    # log(tx.events['LogProcessPayment'])
    received_sums.append(tx.events["LogProcessPayment"]["receivedGwei"])
    refunded_sums.append(tx.events["LogProcessPayment"]["refundedGwei"])
    received_sum += tx.events["LogProcessPayment"]["receivedGwei"]
    refunded_sum += tx.events["LogProcessPayment"]["refundedGwei"]
    log(f"received_sum={received_sum} | refunded_sum={refunded_sum} | job_price={job_price}", "bold")
    log(f"received_sums={received_sums}", "bold")
    log(f"refunded_sums={refunded_sums}", "bold")
    assert job_price - cost["storage"] == received_sum + refunded_sum
    withdraw(accounts[0], received_sum)
    withdraw(requester, refunded_sum)


def test_simple_submit():
    job = Job()
    provider = accounts[0]
    requester = accounts[1]
    price_core_min = 100
    register_provider(price_core_min)
    register_requester(requester)
    job.code_hashes = [b"9b3e9babb65d9c1aceea8d606fc55403", b"9a4c0c1c9aadb203daf9367bd4df930b"]
    job.key = job.code_hashes[0]
    job.cores = [2]
    job.run_time = [1]
    job.data_transfer_ins = [1, 1]
    job.data_transfer_out = 1
    job.storage_ids = [StorageID.EUDAT.value, StorageID.EUDAT.value]
    job.cache_types = [CacheType.PUBLIC.value, CacheType.PUBLIC.value]
    job.storage_hours = [0, 0]
    job.data_prices_set_block_numbers = [0, 0]
    job_price, cost = job.cost(provider, requester)
    provider_price_block_number = ebb.getProviderSetBlockNumbers(accounts[0])[-1]

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
        {"from": requester, "value": to_gwei(job_price)},
    )
    log(f"submitJob_gas_used={tx.__dict__['gas_used']}")
    index = 0
    job_id = 0
    start_timestamp = 1579524978
    tx = ebb.setJobStateRunning(job.key, index, job_id, start_timestamp, {"from": provider})
    gas_costs["setJobStateRunning"].append(tx.__dict__["gas_used"])
    rpc.sleep(60)
    mine(5)

    ended_timestampstamp = 1579524998
    data_transfer_in = 0
    data_transfer_out = 0.01
    elapsed_time = 1
    args = [
        index,
        job_id,
        ended_timestampstamp,
        data_transfer_in,
        data_transfer_out,
        elapsed_time,
        job.cores,
        [1],
        True,
    ]
    out_hash = b"[46\x17\x98r\xc2\xfc\xe7\xfc\xb8\xdd\n\xd6\xe8\xc5\xca$fZ\xebVs\xec\xff\x06[\x1e\xd4f\xce\x99"
    tx = ebb.processPayment(job.key, args, out_hash, {"from": accounts[0]})
    gas_costs["processPayment"].append(tx.__dict__["gas_used"])
    # tx = ebb.processPayment(job.code_hashes[0], args, elapsed_time, zero_bytes32, {"from": accounts[0]})
    received_sum = tx.events["LogProcessPayment"]["receivedGwei"]
    refunded_sum = tx.events["LogProcessPayment"]["refundedGwei"]
    # log(str(received_sum) + " " + str(refunded_sum))
    assert received_sum == job.cores[0] * price_core_min and refunded_sum == 5
    withdraw(accounts[0], received_sum)
    withdraw(requester, refunded_sum)


def test_submit_job():
    job = Job()
    provider = accounts[0]
    requester = accounts[1]
    register_provider()
    register_requester(requester)
    fn = f"{cwd}/files/test.txt"
    # fn = f"{cwd}/files/test_.txt"
    log(f"==> registered_provider_addresses={ebb.getProviders()}")
    provider_price_info = ebb.getProviderInfo(accounts[0], 0)
    # block_read_from = provider_price_info[0]
    _provider_price_info = provider_price_info[1]
    # availableCoreNum = _provider_price_info[0]
    # commitment_block_duration = _provider_price_info[1]
    price_core_min = _provider_price_info[2]
    # price_data_transfer = _provider_price_info[3]
    # price_storage = _provider_price_info[4]
    # price_cache = _provider_price_info[5]
    log(f"provider_available_core={available_core}")
    log(f"provider_price_core_min={price_core_min}")
    log(provider_price_info)
    job_price_sum = 0
    job_id = 0
    index = 0
    with open(fn) as f:
        for line in f:
            arguments = line.rstrip("\n").split(" ")
            storage_hour = 1
            core_min = int(arguments[1]) - int(arguments[0])
            core = int(arguments[2])
            job.cores = [core]
            job.run_time = [core_min]
            # time.sleep(1)
            # rpc.mine(int(arguments[0]))

            job_key = "QmQv4AAL8DZNxZeK3jfJGJi63v1msLMZGan7vSsCDXzZud"
            data_key = "QmQv4AAL8DZNxZeK3jfJGJi63v1msLMZGan7vSsCDXzZud"
            code_hash = ipfs_to_bytes32(data_key)
            # log("Client Balance before: " + str(web3.eth.balanceOf(account)))
            # log("Contract Balance before: " + str(web3.eth.balanceOf(accounts[0])))
            job.code_hashes = [code_hash]
            job.storage_hours = [storage_hour]
            job.data_transfer_ins = [100]
            job.data_transfer_out = 100
            job.data_prices_set_block_numbers = [0]
            job.storage_ids = [StorageID.IPFS.value]
            job.cache_types = [CacheType.PUBLIC.value]
            args = [
                provider,
                ebb.getProviderSetBlockNumbers(accounts[0])[-1],
                job.storage_ids,
                job.cache_types,
                job.data_prices_set_block_numbers,
                job.cores,
                job.run_time,
                job.data_transfer_out,
            ]

            # log(code_hashes[0])
            job_price, *_ = job.cost(provider, requester)
            job_price_sum += job_price
            data_transfer_ins = [100]
            job_key = job.storage_hours[0]
            tx = ebb.submitJob(
                job_key,
                data_transfer_ins,
                args,
                job.storage_hours,
                job.code_hashes,
                {"from": requester, "value": to_gwei(job_price)},
            )
            # log('submitJob => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))
            log(f"job_index={tx.events['LogJob']['index']}", "bold")
            # log("Contract Balance after: " + str(web3.eth.balanceOf(accouts[0])))
            # log("Client Balance after: " + str(web3.eth.balanceOf(accounts[8])))
            # sys.stdout.write('jobInfo: ')
            # sys.stdout.flush()
            log(ebb.getJobInfo(provider, job_key, index, job_id))
            index += 1

    log(f"total_paid={job_price_sum}", "bold")
    # log(block_read_from)
    # rpc.mine(100)
    # log(web3.eth.blockNumber)
    job_id = 0
    with open(fn) as f:
        for index, line in enumerate(f):
            arguments = line.rstrip("\n").split(" ")
            tx = ebb.setJobStateRunning(job_key, index, job_id, int(arguments[0]), {"from": accounts[0]})
            gas_costs["setJobStateRunning"].append(tx.__dict__["gas_used"])
            if index == 0:
                with brownie.reverts():
                    tx = ebb.setJobStateRunning(job_key, index, job_id, int(arguments[0]) + 1, {"from": accounts[0]})
                    gas_costs["setJobStateRunning"].append(tx.__dict__["gas_used"])

    console_ruler()
    result_ipfs_hash = ipfs_to_bytes32("QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Ve")
    with open(fn) as f:
        for index, line in enumerate(f):
            arguments = line.rstrip("\n").split(" ")
            if index == 0:
                data_transfer_in_sum = 90
                job.data_transfer_out = 100
            else:
                data_transfer_in_sum = 0
                job.data_transfer_out = 100

            core_min = int(arguments[1]) - int(arguments[0])
            core = int(arguments[2])
            job.cores = [core]
            job.run_time = [core_min]
            log(f"contract_balance={ebb.getContractBalance()}", "bold")
            job_id = 0
            elapsed_time = int(arguments[1]) - int(arguments[0])
            ended_timestamp = int(arguments[1])
            args = [
                index,
                job_id,
                ended_timestamp,
                data_transfer_in_sum,
                job.data_transfer_out,
                elapsed_time,
                job.cores,
                job.run_time,
                True,
            ]
            tx = ebb.processPayment(job_key, args, result_ipfs_hash, {"from": accounts[0]})
            assert tx.events["LogProcessPayment"]["elapsedTime"] == elapsed_time
            gas_costs["processPayment"].append(tx.__dict__["gas_used"])
            received = tx.events["LogProcessPayment"]["receivedGwei"]
            refunded = tx.events["LogProcessPayment"]["refundedGwei"]
            withdraw(accounts[0], received)
            withdraw(requester, refunded)
            log(f"received={received} | refunded={refunded}", "bold")

    log(f"contract_balance={ebb.getContractBalance()}", "bold")
    for idx in range(0, ebb.getProviderReceiptNode(provider, index)[0]):
        # prints finalize version of the linked list
        log(ebb.getProviderReceiptNode(provider, idx))

    console_ruler()
    log(f"==> storage_duration for job={job_key}")
    *_, job_storage_info = ebb.getStorageInfo(provider, cfg.ZERO_ADDRESS, code_hash)
    ds = DataStorage(job_storage_info)
    log(
        f"received_bn={ds.received_block} |"
        f"storage_duration(block numbers)={ds.storage_duration} | "
        f"is_private={ds.is_private} |"
        f"is_verified_Used={ds.is_verified_used}",
        "bold",
    )
    received_deposit, *_ = ebb.getStorageInfo(provider, requester, code_hash)
    log(f"received_deposit={received_deposit}", "bold")
    for k, v in gas_costs.items():
        print(f"{k} => {v}")


def test_submit_n_data():
    gas_costs = []
    job = Job()
    provider = accounts[0]
    requester = accounts[1]
    price_core_min = 100
    register_provider(price_core_min)
    register_requester(requester)

    job.code_hashes = [b"9b3e9babb65d9c1aceea8d606fc55403"]
    job.key = job.code_hashes[0]
    job.cores = [2]
    job.run_time = [1]
    job.data_transfer_ins = [1]
    job.data_transfer_out = 1
    job.storage_ids = [StorageID.IPFS.value]
    job.cache_types = [CacheType.PUBLIC.value]
    job.storage_hours = [0]
    job.data_prices_set_block_numbers = [0]
    job_price, *_ = job.cost(provider, requester)
    provider_price_block_number = ebb.getProviderSetBlockNumbers(accounts[0])[-1]
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
        {"from": requester, "value": to_gwei(job_price)},
    )
    gas_costs.append(tx.__dict__["gas_used"])
    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    job.code_hashes = [b"9b3e9babb6539c1aceea8d606fc55403", b"9a4c0c1c9aadb203daf9367bd4df930b"]
    job.key = job.code_hashes[0]
    job.cores = [2]
    job.run_time = [1]
    job.data_transfer_ins = [1, 1]
    job.data_transfer_out = 1
    job.storage_ids = [StorageID.EUDAT.value, StorageID.EUDAT.value]
    job.cache_types = [CacheType.PUBLIC.value, CacheType.PUBLIC.value]
    job.storage_hours = [0, 0]
    job.data_prices_set_block_numbers = [0, 0]
    job_price, *_ = job.cost(provider, requester)
    provider_price_block_number = ebb.getProviderSetBlockNumbers(accounts[0])[-1]
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
        {"from": requester, "value": to_gwei(job_price)},
    )
    gas_costs.append(tx.__dict__["gas_used"])
    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    job.code_hashes = [
        b"9b3e9aabb6539c1aczea8d606fc55403",
        b"9a4c0c1c9aadb203daf9367bd4df930b",
        b"9a4c0c1c9aadb203daf1367bd4df930b",
    ]
    job.key = job.code_hashes[0]
    job.cores = [2]
    job.run_time = [1]
    job.data_transfer_ins = [1, 1, 199]
    job.data_transfer_out = 1
    job.storage_ids = [StorageID.GDRIVE.value, StorageID.GDRIVE.value, StorageID.GDRIVE.value]
    job.cache_types = [CacheType.PUBLIC.value, CacheType.PUBLIC.value, CacheType.PUBLIC.value]
    job.storage_hours = [0, 0, 0]
    job.data_prices_set_block_numbers = [0, 0, 0]
    job_price, *_ = job.cost(provider, requester)
    provider_price_block_number = ebb.getProviderSetBlockNumbers(accounts[0])[-1]
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
        {"from": requester, "value": to_gwei(job_price)},
    )
    gas_costs.append(tx.__dict__["gas_used"])
    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    job.code_hashes = [
        b"9b3e9babb6539c1azeea8d606fc55403",
        b"9a4c0c1c9aadb2039af9367bd4df930b",
        b"9a4c0c1c9aadb203daf1367bd4df930b",
        b"9a4c0c1c9aadb203daf1167bd4df930b",
    ]
    job.key = job.code_hashes[0]
    job.cores = [2]
    job.run_time = [1]
    job.data_transfer_ins = [1, 1, 199, 200]
    job.data_transfer_out = 1
    job.storage_ids = [StorageID.IPFS.value, StorageID.IPFS.value, StorageID.IPFS.value, StorageID.IPFS.value]
    job.cache_types = [
        CacheType.PUBLIC.value,
        CacheType.PUBLIC.value,
        CacheType.PUBLIC.value,
        CacheType.PUBLIC.value,
    ]
    job.storage_hours = [0, 0, 0, 1]
    job.data_prices_set_block_numbers = [0, 0, 0, 0]
    job_price, *_ = job.cost(provider, requester)
    provider_price_block_number = ebb.getProviderSetBlockNumbers(accounts[0])[-1]
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
        {"from": requester, "value": to_gwei(job_price)},
    )
    gas_costs.append(tx.__dict__["gas_used"])

    print(gas_costs)
    print(gas_costs[1] - gas_costs[0])
    print(gas_costs[2] - gas_costs[1])
    print(gas_costs[3] - gas_costs[2])
