#!/usr/bin/python3

import atexit
import os
import pytest
import sys
from os import path
import atexit

import brownie
import contract.tests.cfg as _cfg
from broker import cfg, config
from broker._utils._log import console_ruler
from broker.config import setup_logger
from broker.eblocbroker_scripts import Contract
from broker.eblocbroker_scripts.job import DataStorage, Job
from broker.eblocbroker_scripts.utils import Cent
from broker.utils import CacheType, StorageID, ipfs_to_bytes32, log, zero_bytes32
from brownie import accounts, rpc, web3
from brownie.network.state import Chain
from contract.scripts.lib import gas_costs, mine, new_test

COMMITMENT_BN = 600
Contract.eblocbroker = Contract.Contract(is_brownie=True)

# from brownie.test import given, strategy
setup_logger("", True)
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
cwd = os.getcwd()
provider_gmail = "provider_test@gmail.com"
fid = "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu"
price_core_min = Cent("1 cent")
price_data_transfer_mb = Cent("1 cent")
price_storage_hr = Cent("1 cent")
price_cache_mb = Cent("1 cent")
prices = [price_core_min, price_data_transfer_mb, price_storage_hr, price_cache_mb]

GPG_FINGERPRINT = "0359190A05DF2B72729344221D522F92EFA2F330"
ipfs_address = "/ip4/79.123.177.145/tcp/4001/ipfs/QmWmZQnb8xh3gHf9ZFmVQC4mLEav3Uht5kHJxZtixG3rsf"
Ebb = None
chain = None
ebb = None


def print_gas_costs():
    """Cleanup a testing directory once we are finished."""
    log("average_gas_costs=",end="")
    gas_costs_items_temp = {}
    for k, v in gas_costs.items():
        if v:
            gas_costs_items_temp[k] = int(sum(v) / len(v))

    log(dict(gas_costs_items_temp))


def append_gas_cost(func_n, tx):
    gas_costs[func_n].append(tx.__dict__["gas_used"])


@pytest.fixture(scope="session", autouse=True)
def cleanup():
    """Cleanup a testing directory once we are finished."""
    print_gas_costs()


@pytest.fixture(scope="module", autouse=True)
def my_own_session_run_at_beginning(_Ebb):
    global Ebb, chain, ebb  # type: ignore

    cfg.IS_BROWNIE_TEST = True
    config.Ebb = Ebb = Contract.Contract(is_brownie=True)
    #
    config.ebb = _Ebb
    Contract.eblocbroker.eBlocBroker = _Ebb
    ebb = _Ebb
    #
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
    log(f"bn={web3.eth.blockNumber} | contract_bn={web3.eth.blockNumber + 1}")
    return web3.eth.blockNumber


def get_block_timestamp():
    return web3.eth.getBlock(get_block_number()).timestamp


def register_provider(price_core_min=Cent("1 cent"), available_core: int = None, prices=None):
    """Register Provider"""
    ebb = config.ebb
    if not _cfg.OWNER:
        _cfg.OWNER = accounts[0]

    mine(1)
    provider_account = accounts[1]
    assert ebb.getOwner() != provider_account  # contract owner could not be a provider
    if not prices:
        prices = [price_core_min, price_data_transfer_mb, price_storage_hr, price_cache_mb]

    tx = config.ebb.registerProvider(
        GPG_FINGERPRINT,
        provider_gmail,
        fid,
        ipfs_address,
        available_core,
        prices,
        COMMITMENT_BN,
        {"from": provider_account},
    )
    append_gas_cost("registerProvider", tx)
    provider_registered_bn = tx.block_number
    log(f"block number when the provider is registered={provider_registered_bn}")
    gpg_fingerprint = remove_zeros_gpg_fingerprint(tx.events["LogProviderInfo"]["gpgFingerprint"])
    assert gpg_fingerprint == GPG_FINGERPRINT
    log(f"==> gpg_fingerprint={gpg_fingerprint}")
    orc_id = "0000-0001-7642-0442"
    orc_id_as_bytes = str.encode(orc_id)

    assert ebb.isOrcIDVerified(provider_account) is False, "orc_id initial value should be false"

    tx = ebb.authenticateOrcID(provider_account, orc_id_as_bytes, {"from": _cfg.OWNER})
    append_gas_cost("authenticateOrcID", tx)
    assert ebb.isOrcIDVerified(provider_account) is True, "isOrcIDVerified() is failed"
    # orc_id should only set once for the same user
    with brownie.reverts():
        tx = ebb.authenticateOrcID(provider_account, orc_id_as_bytes, {"from": _cfg.OWNER})

    assert orc_id == ebb.getOrcID(provider_account).decode("utf-8").replace("\x00", ""), "orc_id set false"
    return provider_registered_bn


def register_requester(account):
    """Register requester."""
    ebb = config.ebb
    if not _cfg.OWNER:
        _cfg.OWNER = accounts[0]

    tx = ebb.registerRequester(
        GPG_FINGERPRINT,
        "alper.alimoglu@gmail.com",
        fid,
        "/ip4/79.123.177.145/tcp/4001/ipfs/QmWmZQnb8xh3gHf9ZFmVQC4mLEav3Uht5kHJxZtixG3rsf",
        {"from": account},
    )
    append_gas_cost("registerRequester", tx)
    assert ebb.doesRequesterExist(account), True
    gpg_fingerprint = remove_zeros_gpg_fingerprint(tx.events["LogRequester"]["gpgFingerprint"])
    assert gpg_fingerprint == GPG_FINGERPRINT
    orc_id = "0000-0001-7642-0552"
    orc_id_as_bytes = str.encode(orc_id)
    assert ebb.isOrcIDVerified(account) is False, "orc_id initial value should be false"
    #
    tx = ebb.authenticateOrcID(account, orc_id_as_bytes, {"from": _cfg.OWNER})  # ORCID should be registered.
    assert ebb.isOrcIDVerified(account), "isOrcIDVerified is failed"
    assert not ebb.isOrcIDVerified(accounts[9]), "isOrcIDVerified is failed"
    with brownie.reverts():  # orc_id should only set once for the same user
        ebb.authenticateOrcID(account, orc_id_as_bytes, {"from": _cfg.OWNER})

    assert orc_id == ebb.getOrcID(account).decode("utf-8").replace("\x00", ""), "orc_id set false"


def _transfer(to, amount):
    ebb.transfer(to, Cent(amount), {"from": _cfg.OWNER})


def set_transfer(to, amount):
    """Empty balance and transfer given amount."""
    balance = ebb.balanceOf(to)
    ebb.approve(accounts[0], balance, {"from": to})
    ebb.transferFrom(to, accounts[0], balance, {"from": _cfg.OWNER})
    assert ebb.balanceOf(to) == 0
    ebb.transfer(to, Cent(amount), {"from": _cfg.OWNER})


# # @pytest.mark.skip(reason="skip")
# def test_dummy():
#     print("skip me")


# =========== testing starts ======================== #


def test_total_supply():
    total_supply = "1000000000 usd"
    assert ebb.balanceOf(_cfg.OWNER) == Cent(total_supply)


def test_register():
    _prices = [Cent("0.5 usdt"), Cent("1 usdt"), Cent("4 cent"), Cent("0.1 usdt")]
    register_provider(prices=_prices, available_core=128)
    provider_price_info = ebb.getProviderInfo(accounts[1], 0)
    assert provider_price_info[1][2:] == _prices
    requester = accounts[2]
    register_requester(requester)

    ebb.transfer(requester, Cent("100 usd"), {"from": accounts[0]})
    assert ebb.balanceOf(requester) == Cent("100 usd")


def test_stored_data_usage():
    provider = accounts[1]
    requester = accounts[2]
    requester_1 = accounts[3]
    register_provider(Cent("10 cent"), available_core=128)
    register_requester(requester)
    register_requester(requester_1)

    # ebb.transfer(accounts[1], amount, {"from": accounts[0]})
    job = Job()
    job.code_hashes.append(b"050e6cc8dd7e889bf7874689f1e1ead6")
    job.code_hashes.append(b"b6aaf03752dc68d625fc57b451faa2bf")
    job.data_transfer_ins = [1, 1]
    job.data_transfer_out = 1
    job.storage_hours = [1, 1]
    job.data_prices_set_block_numbers = [0, 0]
    job.cores = [1]
    job.run_time = [5]
    job.provider_price_bn = ebb.getProviderSetBlockNumbers(provider)[-1]
    job.storage_ids = [StorageID.GDRIVE.value, StorageID.GDRIVE.value]
    job.cache_types = [CacheType.PUBLIC.value, CacheType.PRIVATE.value]
    job_price, cost = job.cost(provider, requester)
    log(f"price={float(Cent(job_price).to('usd'))} usd")
    args = [
        provider,
        job.provider_price_bn,
        job.storage_ids,
        job.cache_types,
        job.data_prices_set_block_numbers,
        job.cores,
        job.run_time,
        job.data_transfer_out,
        job_price,
    ]
    # first time job is submitted with the data files
    # https://stackoverflow.com/a/12468284/2402577
    ###############################
    _transfer(requester, Cent(job_price))
    tx = ebb.submitJob(
        job.code_hashes[0],
        job.data_transfer_ins,
        args,
        job.storage_hours,
        job.code_hashes,
        {"from": requester},
    )
    assert Cent(ebb.balanceOf(requester)) == 0
    # assert Cent(ebb.balanceOf(requester)).__add__(job_price) == Cent("100 usd")
    log(tx.events["LogDataStorageRequest"]["owner"])
    key = tx.events["LogJob"]["jobKey"]
    assert tx.events["LogJob"]["received"] == Cent(job_price)
    log(f"==> job_index={tx.events['LogJob']['index']} | key={key}")
    assert cost["storage"] == 2 * Cent("1 cent")
    job_price, cost = job.cost(provider, requester)
    log(f"==> key={tx.events['LogJob']['jobKey']} | job_index={tx.events['LogJob']['index']}")
    assert cost["storage"] == 0, "Since it is not verified yet cost of storage should be 2"
    assert cost["data_transfer"] == 1 * Cent("1 cent")
    with brownie.reverts():
        #: job price is changed
        job_price_minus_one = job_price - 1
        _transfer(requester, Cent(job_price_minus_one))
        args[-1] = job_price_minus_one  # data_transfer_in cost is ignored
        tx = ebb.submitJob(
            job.code_hashes[0],
            job.data_transfer_ins,
            args,
            job.storage_hours,
            job.code_hashes,
            {"from": requester},
        )
        # log(dict(tx.events["LogJob"]))
        # log(tx.events["LogJob"]["received"] - tx.events["LogJob"]["refunded"])

    log(f"#> measured_job_price={job_price}")
    set_transfer(requester, Cent(job_price))
    args[-1] = job_price
    tx = ebb.submitJob(
        job.code_hashes[0],
        job.data_transfer_ins,
        args,
        job.storage_hours,
        job.code_hashes,
        {"from": requester},
    )
    assert Cent(ebb.balanceOf(requester)) == 0
    assert "LogDataStorageRequest" not in tx.events
    mine(cfg.ONE_HOUR_BLOCK_DURATION)
    job_price, cost = job.cost(provider, requester)
    args[-1] = job_price
    # first time job is submitted with the data files
    _transfer(requester, Cent(job_price))
    tx = ebb.submitJob(
        job.code_hashes[0],
        job.data_transfer_ins,
        args,
        job.storage_hours,
        job.code_hashes,
        {"from": requester},
    )
    assert "LogDataStorageRequest" not in tx.events


def test_data_info():
    job = Job()
    provider = accounts[1]
    requester = accounts[2]
    register_provider(Cent("100 cent"), available_core=128)
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
    provider_price_bn = ebb.getProviderSetBlockNumbers(provider)[-1]
    args = [
        provider,
        provider_price_bn,
        job.storage_ids,
        job.cache_types,
        job.data_prices_set_block_numbers,
        job.cores,
        job.run_time,
        job.data_transfer_out,
        job_price,
    ]
    _transfer(requester, Cent(job_price))
    ebb.submitJob(
        job_key,
        job.data_transfer_ins,
        args,
        job.storage_hours,
        job.code_hashes,
        {"from": requester},
    )
    assert Cent(ebb.balanceOf(requester)) == 0
    provider_price_info = ebb.getProviderInfo(provider, 0)
    price_cache_mb = provider_price_info[1][4]
    storage_payment = []
    for idx, code_hash in enumerate(job.code_hashes):
        deposit, *_ = ebb.getStorageInfo(provider, requester, code_hash)
        storage_payment.append(deposit)
        assert storage_payment[idx] == job.storage_hours[idx] * price_cache_mb

    job.is_verified = [False, True]
    tx = ebb.setDataVerified([job.code_hashes[1]], {"from": provider})
    for idx, code_hash in enumerate(job.code_hashes):
        *_, output = ebb.getStorageInfo(provider, cfg.ZERO_ADDRESS, code_hash)
        assert output[3] == job.is_verified[idx]
        # requester is data_owner

    for idx, code_hash in enumerate(job.code_hashes):
        with brownie.reverts():
            tx = ebb.depositStorage(requester, code_hash, {"from": provider})
            append_gas_cost("depositStorage", tx)

    mine(cfg.ONE_HOUR_BLOCK_DURATION)
    for idx, code_hash in enumerate(job.code_hashes):
        *_, output = ebb.getStorageInfo(provider, cfg.ZERO_ADDRESS, code_hash)
        if output[3]:
            tx = ebb.depositStorage(requester, code_hash, {"from": provider})
            append_gas_cost("depositStorage", tx)
            print(tx.events["LogDepositStorage"])


def test_computational_refund():
    job = Job()
    provider = accounts[1]
    requester = accounts[2]
    register_provider(Cent("100 cent"), available_core=128)
    register_requester(requester)
    job.code_hashes = [b"9b3e9babb65d9c1aceea8d606fc55403", b"9a4c0c1c9aadb203daf9367bd4df930b"]
    job.cores = [1]
    job.run_time = [5]
    job.data_transfer_ins = [1, 1]
    job.data_transfer_out = 1
    job.storage_ids = [StorageID.B2DROP.value, StorageID.B2DROP.value]
    job.cache_types = [CacheType.PUBLIC.value, CacheType.PUBLIC.value]
    job.storage_hours = [0, 0]
    job.data_prices_set_block_numbers = [0, 0]
    job_price, *_ = job.cost(provider, requester)
    provider_price_bn = ebb.getProviderSetBlockNumbers(provider)[-1]
    args = [
        provider,
        provider_price_bn,
        job.storage_ids,
        job.cache_types,
        job.data_prices_set_block_numbers,
        job.cores,
        job.run_time,
        job.data_transfer_out,
        job_price,
    ]
    _transfer(requester, Cent(job_price))
    tx = ebb.submitJob(
        job.code_hashes[0],
        job.data_transfer_ins,
        args,
        job.storage_hours,
        job.code_hashes,
        {"from": requester},
    )
    index = 0
    job_id = 0
    start_ts = 1579524978
    tx = ebb.setJobStateRunning(job.code_hashes[0], index, job_id, start_ts, {"from": provider})
    append_gas_cost("setJobStateRunning", tx)
    rpc.sleep(60)
    mine(5)
    run_time = 1
    args = [index, job_id, 1579524998, 2, 0, run_time, job.cores, [5]]
    tx = ebb.processPayment(job.code_hashes[0], args, zero_bytes32, {"from": provider})
    received_sum = tx.events["LogProcessPayment"]["receivedCent"]
    refunded_sum = tx.events["LogProcessPayment"]["refundedCent"]
    assert tx.events["LogProcessPayment"]["elapsedTime"] == run_time
    log(f"{received_sum} {refunded_sum}")
    assert received_sum + refunded_sum == job_price
    assert received_sum == 104 * Cent("1 cent") and refunded_sum == 401 * Cent("1 cent")


def test_storage_refund():
    job = Job()
    provider = accounts[1]
    requester = accounts[2]
    register_provider(available_core=128)
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
    job.provider_price_bn = ebb.getProviderSetBlockNumbers(provider)[-1]
    job.storage_ids = [StorageID.B2DROP.value, StorageID.IPFS.value]
    job.cache_types = [CacheType.PRIVATE.value, CacheType.PUBLIC.value]
    job.data_prices_set_block_numbers = [0, 0]  # provider's registered data won't be used
    job_price, cost = job.cost(provider, requester)
    job_price += 1  # for test additional 1 Gwei is paid
    args = [
        provider,
        job.provider_price_bn,
        job.storage_ids,
        job.cache_types,
        job.data_prices_set_block_numbers,
        job.cores,
        job.run_time,
        job.data_transfer_out,
        job_price,
    ]
    _transfer(requester, Cent(job_price))
    tx = ebb.submitJob(
        job_key,
        job.data_transfer_ins,
        args,
        job.storage_hours,
        job.code_hashes,
        {"from": requester},
    )
    refunded = tx.events["LogJob"]["refunded"]
    assert ebb.balanceOf(requester) == refunded == 1
    log(f"==> key={tx.events['LogJob']['jobKey']} | job_index={tx.events['LogJob']['index']}")
    assert requester == tx.events["LogJob"]["owner"]
    index = 0
    job_id = 0
    tx = ebb.refund(provider, job_key, index, job_id, job.cores, job.run_time, {"from": provider})
    append_gas_cost("refund", tx)
    log(ebb.getJobInfo(provider, job_key, index, job_id))
    refunded_cent = tx.events["LogRefundRequest"]["refundedCent"]
    log(f"refunded_cent={refunded_cent}")

    assert ebb.balanceOf(requester) == 320 * Cent("1 cent") + refunded
    # withdraw(requester, refunded_cent)
    # VM Exception while processing transaction: invalid opcode
    with brownie.reverts():
        ebb.getJobInfo(provider, job_key, 5, job_id)

    storage_cost_sum = 0
    for code_hash in job.code_hashes:
        _storage_cost_sum, *_ = ebb.getStorageInfo(provider, requester, code_hash)
        storage_cost_sum += _storage_cost_sum

    assert cost["storage"] == storage_cost_sum
    assert cost["computational"] + cost["data_transfer"] + cost["cache"] == refunded_cent
    mine(cfg.ONE_HOUR_BLOCK_DURATION)
    tx = ebb.refundStorageDeposit(provider, requester, job.code_hashes[0], {"from": requester})
    append_gas_cost("refundStorageDeposit", tx)
    refunded_cent = tx.events["LogDepositStorage"]["payment"]
    log(f"refunded_cent={refunded_cent}")
    assert ebb.balanceOf(requester) == 420 * Cent("1 cent") + refunded
    # withdraw(requester, refunded_cent)
    with brownie.reverts():
        tx = ebb.refundStorageDeposit(provider, requester, job.code_hashes[0], {"from": requester})

    tx = ebb.refundStorageDeposit(provider, requester, job.code_hashes[1], {"from": requester})
    append_gas_cost("refundStorageDeposit", tx)
    refunded_cent = tx.events["LogDepositStorage"]["payment"]
    paid_address = tx.events["LogDepositStorage"]["paidAddress"]
    assert ebb.balanceOf(requester) == job_price
    # withdraw(requester, refunded_cent)
    with brownie.reverts():
        tx = ebb.refundStorageDeposit(provider, requester, job.code_hashes[0], {"from": requester})

    assert requester == paid_address
    assert ebb.balanceOf(provider) == 0
    console_ruler("same job submitted after full refund", color="blue")
    args[-1] = job_price
    set_transfer(requester, Cent(job_price))
    tx = ebb.submitJob(
        job_key,
        job.data_transfer_ins,
        args,
        job.storage_hours,
        job.code_hashes,
        {"from": requester},
    )
    log(f"==> key={tx.events['LogJob']['jobKey']} | job_index={tx.events['LogJob']['index']}")
    index = 1
    job_id = 0
    tx = ebb.refund(provider, job_key, index, job_id, job.cores, job.run_time, {"from": provider})
    append_gas_cost("refund", tx)
    log(ebb.getJobInfo(provider, job_key, index, job_id))
    refunded_cent = tx.events["LogRefundRequest"]["refundedCent"]
    assert cost["computational"] + cost["data_transfer"] + cost["cache"] == refunded_cent
    storage_cost_sum = 0
    storage_payment = []
    for code_hash in job.code_hashes:
        deposit, *_ = ebb.getStorageInfo(provider, requester, code_hash)
        storage_payment.append(deposit)

    job.is_verified = [True, True]
    tx = ebb.setDataVerified(job.code_hashes, {"from": provider})
    append_gas_cost("setDataVerified", tx)
    # ebb.dataReceived(  # called by the provider
    #     job_key, index, job.code_hashes, job.cache_types, job.is_verified, {"from": provider}
    # )
    for code_hash in job.code_hashes:
        *_, output = ebb.getStorageInfo(provider, cfg.ZERO_ADDRESS, code_hash)
        log(output, "bold")

    with brownie.reverts():  # refundStorageDeposit should revert, because it is already used by the provider
        for code_hash in job.code_hashes:
            tx = ebb.refundStorageDeposit(provider, requester, code_hash, {"from": requester})

        tx = ebb.depositStorage(requester, job.code_hashes[0], {"from": provider})

    mine(cfg.ONE_HOUR_BLOCK_DURATION)
    # after deadline (1 hr) is completed to store the data, provider could obtain the money
    for idx, code_hash in enumerate(job.code_hashes):
        initial_balance = ebb.balanceOf(provider)
        tx = ebb.depositStorage(requester, code_hash, {"from": provider})
        append_gas_cost("depositStorage", tx)
        amount = tx.events["LogDepositStorage"]["payment"]
        assert (ebb.balanceOf(provider) - initial_balance) == amount
        assert storage_payment[idx] == amount


def test_update_provider():
    provider = accounts[1]
    mine(5)
    provider_registered_bn = register_provider(available_core=128)
    tx = ebb.updateProviderInfo(GPG_FINGERPRINT, provider_gmail, fid, ipfs_address, {"from": provider})
    append_gas_cost("updateProviderInfo", tx)
    log(ebb.getUpdatedProviderPricesBlocks(provider))
    available_core = 64
    prices = [Cent("5 cent"), 2, 2, 2]
    tx = ebb.updateProviderPrices(available_core, COMMITMENT_BN, prices, {"from": provider})
    append_gas_cost("updateProviderPrices", tx)

    prices = [3, 3, 3, 3]  # update prices right away to check overwrite
    tx = ebb.updateProviderPrices(available_core, COMMITMENT_BN, prices, {"from": provider})
    append_gas_cost("updateProviderPrices", tx)

    prices = [4, 4, 4, 4]  # update prices right away to check overwrite
    tx = ebb.updateProviderPrices(available_core, COMMITMENT_BN, prices, {"from": provider})
    append_gas_cost("updateProviderPrices", tx)

    prices_set_block_number = ebb.getUpdatedProviderPricesBlocks(provider)
    provider_info = ebb.getProviderInfo(provider, prices_set_block_number[-1])
    assert 4 == provider_info[1][2] == provider_info[1][3] == provider_info[1][4] == provider_info[1][5]
    provider_info = ebb.getProviderInfo(provider, prices_set_block_number[0])
    assert (
        1 * Cent("1 cent") == provider_info[1][2] == provider_info[1][3] == provider_info[1][4] == provider_info[1][5]
    )

    available_core = 128
    tx = ebb.updateProviderPrices(available_core, COMMITMENT_BN, prices, {"from": provider})
    append_gas_cost("updateProviderPrices", tx)

    prices_set_block_number = ebb.getUpdatedProviderPricesBlocks(provider)[1]
    assert ebb.getProviderInfo(provider, prices_set_block_number)[1][0] == 128

    available_core = 16
    tx = ebb.updateProviderPrices(available_core, COMMITMENT_BN, prices, {"from": provider})
    append_gas_cost("updateProviderPrices", tx)

    prices_set_block_number = ebb.getUpdatedProviderPricesBlocks(provider)[1]
    assert ebb.getProviderInfo(provider, prices_set_block_number)[1][0] == 16
    mine(cfg.ONE_HOUR_BLOCK_DURATION)

    available_core = 32
    tx = ebb.updateProviderPrices(available_core, COMMITMENT_BN, prices, {"from": provider})
    append_gas_cost("updateProviderPrices", tx)

    log(ebb.getUpdatedProviderPricesBlocks(provider))
    assert ebb.getUpdatedProviderPricesBlocks(provider)[2] == COMMITMENT_BN * 2 + provider_registered_bn

    provider_price_info = ebb.getProviderInfo(provider, 0)
    block_read_from = provider_price_info[0]
    assert block_read_from == COMMITMENT_BN + provider_registered_bn


def test_multiple_data():
    job = Job()
    provider = accounts[1]
    requester = accounts[2]
    requester_1 = accounts[3]
    register_provider(available_core=128)
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
    provider_price_bn = ebb.getProviderSetBlockNumbers(provider)[-1]
    job.storage_ids = [StorageID.B2DROP.value, StorageID.IPFS.value]
    job.cache_types = [CacheType.PRIVATE.value, CacheType.PUBLIC.value]
    job_price, cost = job.cost(provider, requester)
    args = [
        provider,
        provider_price_bn,
        job.storage_ids,
        job.cache_types,
        job.data_prices_set_block_numbers,
        job.cores,
        job.run_time,
        job.data_transfer_out,
        job_price,
    ]

    # first time job is submitted with the data files
    _transfer(requester, Cent(job_price))
    tx = ebb.submitJob(
        job_key,
        job.data_transfer_ins,
        args,
        job.storage_hours,
        job.code_hashes,
        {"from": requester},
    )
    log(f"==> key={tx.events['LogJob']['jobKey']} | job_index={tx.events['LogJob']['index']}")
    assert cost["storage"] == 200 * Cent("1 cent"), "Since it is not verified yet cost of storage should be 200"

    # second time job is wanted to send by the same user  with the same data files
    job_price, cost = job.cost(provider, requester)
    assert cost["storage"] == 0, "Since cost of storage is already paid by the user it should be 0"

    # second time job is wanted to send by the differnt user  with the same data files
    job_price, cost = job.cost(provider, requester_1)
    log(f"==> cost={cost}")
    assert cost["storage"] == 200 * Cent("1 cent"), "Since it is not verified yet cost of storage should be 200"
    # cluster verifies the given data files for the related job
    index = 0
    # is_verified_list = [True, True]
    tx = ebb.setDataVerified(job.code_hashes, {"from": provider})
    append_gas_cost("withdraw", tx)
    gas_costs["setDataVerified"].append(tx.__dict__["gas_used"])
    tx = ebb.setDataPublic(
        job_key,
        index,
        job.code_hashes,
        job.cache_types,
        {"from": provider},
    )
    #: second time job is wanted to send by the differnt user  with the same data files
    job_price, cost = job.cost(provider, requester)
    assert cost["storage"] == 0, "Since it is verified storageCost should be 0"
    #: second time job is wanted to send by the differnt user  with the same data files
    job_price, cost = job.cost(provider, requester_1)
    assert cost["storage"] == 100 * Cent(
        "1 cent"
    ), "Since data1 is verified and public, its cost of storage should be 0"
    # ds = scripts.DataStorage(provider, code_hashes[1], True)
    job_price, cost = job.cost(provider, requester)
    assert cost["storage"] == 0, "Since it is paid on first job submittion it should be 0"
    assert cost["data_transfer"] == job.data_transfer_out * Cent(
        "1 cent"
    ), "cost of data_transfer should cover only data_transfer_out"
    args[-1] = job_price
    set_transfer(requester, Cent(job_price))
    tx = ebb.submitJob(
        job_key,
        job.data_transfer_ins,
        args,
        job.storage_hours,
        job.code_hashes,
        {"from": requester},
    )
    # log(f"job_index={tx.events['LogJob']['index']}")
    # ===== provider side =====
    index = 0
    job_id = 0
    elapsed_time = 10
    result_ipfs_hash = "0xabcd"
    start_ts = get_block_timestamp()
    tx = ebb.setJobStateRunning(job_key, index, job_id, start_ts, {"from": provider})
    append_gas_cost("setJobStateRunning", tx)
    mine(60 * elapsed_time / cfg.BLOCK_DURATION + 1)
    end_ts = start_ts + 60 * elapsed_time
    block_timestamp = get_block_timestamp()
    assert (
        end_ts <= block_timestamp
    ), f"block timestamp is ahead of timestamp of when the job ended, difference={block_timestamp - end_ts}"
    args = [
        index,
        job_id,
        end_ts,
        sum(job.data_transfer_ins),
        job.data_transfer_out,
        elapsed_time,
        job.cores,
        job.run_time,
    ]
    tx = ebb.processPayment(job_key, args, result_ipfs_hash, {"from": provider})
    assert tx.events["LogProcessPayment"]["elapsedTime"] == elapsed_time
    received_sum = tx.events["LogProcessPayment"]["receivedCent"]
    refunded_sum = tx.events["LogProcessPayment"]["refundedCent"]
    log(f"received={received_sum} refunded={refunded_sum}")
    assert received_sum == 320 * Cent("1 cent") and refunded_sum == 0
    assert Cent(ebb.balanceOf(provider)) == received_sum
    assert Cent(ebb.balanceOf(requester)) == refunded_sum

    set_transfer(provider, Cent(0))  # clean provider balance

    data_transfer_in = 0  # already requested on index==0
    data_transfer_out = 100
    data_transfer = [data_transfer_in, data_transfer_out]
    index = 1
    job_id = 0
    start_ts = get_block_timestamp()
    elapsed_time = 10
    result_ipfs_hash = "0xabcd"
    tx = ebb.setJobStateRunning(job_key, index, job_id, start_ts, {"from": provider})
    append_gas_cost("setJobStateRunning", tx)
    mine(60 * elapsed_time / cfg.BLOCK_DURATION)
    end_ts = start_ts + 60 * elapsed_time
    args = [index, job_id, end_ts, data_transfer[0], data_transfer[1], elapsed_time, job.cores, job.run_time]
    tx = ebb.processPayment(job_key, args, result_ipfs_hash, {"from": provider})
    assert tx.events["LogProcessPayment"]["elapsedTime"] == elapsed_time
    append_gas_cost("processPayment", tx)
    # log(tx.events['LogProcessPayment'])
    received_sum = tx.events["LogProcessPayment"]["receivedCent"]
    refunded_sum = tx.events["LogProcessPayment"]["refundedCent"]
    log(f"#> received={received_sum} refunded={refunded_sum}")
    assert received_sum == 120 * Cent("1 cent") and refunded_sum == 0
    assert Cent(ebb.balanceOf(provider)) == received_sum
    assert Cent(ebb.balanceOf(requester)) == refunded_sum


def test_simple_submit():
    job = Job()
    provider = accounts[1]
    requester = accounts[2]
    price_core_min = Cent("1 cent")
    register_provider(price_core_min, available_core=128)
    register_requester(requester)
    job.code_hashes = [b"9b3e9babb65d9c1aceea8d606fc55403", b"9a4c0c1c9aadb203daf9367bd4df930b"]
    job.key = job.code_hashes[0]
    job.cores = [2]
    job.run_time = [1]
    job.data_transfer_ins = [1, 1]
    job.data_transfer_out = 1
    job.storage_ids = [StorageID.B2DROP.value, StorageID.B2DROP.value]
    job.cache_types = [CacheType.PUBLIC.value, CacheType.PUBLIC.value]
    job.storage_hours = [0, 0]
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
    assert Cent(ebb.balanceOf(_cfg.OWNER)) == Cent("1000000000 usd")
    log(f"submit_job_gas_used={tx.__dict__['gas_used']}")
    index = 0
    job_id = 0
    start_ts = 1579524978
    tx = ebb.setJobStateRunning(job.key, index, job_id, start_ts, {"from": provider})
    append_gas_cost("setJobStateRunning", tx)
    rpc.sleep(60)
    mine(5)

    ended_ts = 1579524998
    data_transfer_in = 0
    data_transfer_out = 0.01
    elapsed_time = 1
    args = [
        index,
        job_id,
        ended_ts,
        data_transfer_in,
        data_transfer_out,
        elapsed_time,
        job.cores,
        [1],
    ]
    out_hash = b"[46\x17\x98r\xc2\xfc\xe7\xfc\xb8\xdd\n\xd6\xe8\xc5\xca$fZ\xebVs\xec\xff\x06[\x1e\xd4f\xce\x99"
    tx = ebb.processPayment(job.key, args, out_hash, {"from": provider})
    append_gas_cost("processPayment", tx)
    # tx = ebb.processPayment(job.code_hashes[0], args, elapsed_time, zero_bytes32, {"from": accounts[0]})
    received_sum = tx.events["LogProcessPayment"]["receivedCent"]
    refunded_sum = tx.events["LogProcessPayment"]["refundedCent"]
    # log(str(received_sum) + " " + str(refunded_sum))
    assert received_sum == job.cores[0] * price_core_min and refunded_sum == 5 * Cent("1 cent")
    assert Cent(ebb.balanceOf(provider)) == received_sum
    assert Cent(ebb.balanceOf(requester)) == refunded_sum
    assert Cent(ebb.balanceOf(_cfg.OWNER)) == Cent("1000000000 usd").__sub__(job_price)


def test_submit_jobs():
    job = Job()
    provider = accounts[1]
    requester = accounts[2]
    a_core = 128
    register_provider(available_core=a_core)
    register_requester(requester)
    fn = f"{cwd}/files/test.txt"
    # fn = f"{cwd}/files/_test.txt"
    log(f"==> registered_provider_addresses={ebb.getProviders()}")
    provider_price_info = ebb.getProviderInfo(provider, 0)
    # block_read_from = provider_price_info[0]
    _provider_price_info = provider_price_info[1]
    # availableCoreNum = _provider_price_info[0]
    # commitment_block_duration = _provider_price_info[1]
    price_core_min = _provider_price_info[2]
    # price_data_transfer_mb = _provider_price_info[3]
    # price_storage_hr = _provider_price_info[4]
    # price_cache_mb = _provider_price_info[5]
    log(f"provider_available_core={a_core}")
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
            # log(code_hashes[0])
            job_price, *_ = job.cost(provider, requester)
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
            job_price_sum += job_price
            data_transfer_ins = [100]
            job_key = job.storage_hours[0]

            set_transfer(requester, Cent(job_price))
            tx = ebb.submitJob(
                job_key,
                data_transfer_ins,
                args,
                job.storage_hours,
                job.code_hashes,
                {"from": requester},
            )
            # log(f"job_index={tx.events['LogJob']['index']}")
            # log('submitJob => GasUsed:' + str(tx.__dict__['gas_used']) + '| blockNumber=' + str(tx.block_number))
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
            tx = ebb.setJobStateRunning(job_key, index, job_id, int(arguments[0]), {"from": provider})
            append_gas_cost("setJobStateRunning", tx)
            if index == 0:
                with brownie.reverts():
                    tx = ebb.setJobStateRunning(job_key, index, job_id, int(arguments[0]) + 1, {"from": provider})
                    append_gas_cost("setJobStateRunning", tx)

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
            log(f"contract_balance={Cent(ebb.balanceOf(_cfg.OWNER))}")
            job_id = 0
            elapsed_time = int(arguments[1]) - int(arguments[0])
            end_ts = int(arguments[1])
            args = [
                index,
                job_id,
                end_ts,
                data_transfer_in_sum,
                job.data_transfer_out,
                elapsed_time,
                job.cores,
                job.run_time,
            ]
            set_transfer(provider, Cent(0))  # clean provider balance
            set_transfer(requester, Cent(0))  # clean requester balance
            tx = ebb.processPayment(job_key, args, result_ipfs_hash, {"from": provider})
            assert tx.events["LogProcessPayment"]["elapsedTime"] == elapsed_time
            append_gas_cost("processPayment", tx)
            received = tx.events["LogProcessPayment"]["receivedCent"]
            refunded = tx.events["LogProcessPayment"]["refundedCent"]
            assert Cent(ebb.balanceOf(provider)) == received
            assert Cent(ebb.balanceOf(requester)) == refunded
            log(f"received={received} | refunded={refunded}")

    log(f"contract_balance={Cent(ebb.balanceOf(_cfg.OWNER))}")
    for idx in range(0, ebb.getProviderReceiptNode(provider, index)[0]):
        # prints finalize version of the linked list
        log(ebb.getProviderReceiptNode(provider, idx))

    console_ruler()
    log(f"==> storage_duration for job={job_key}")
    *_, job_storage_info = ebb.getStorageInfo(provider, cfg.ZERO_ADDRESS, code_hash)
    ds = DataStorage(job_storage_info)
    log(
        f"received_bn={ds.received_block} | "
        f"storage_duration(block numbers)={ds.storage_duration} | "
        f"is_private={ds.is_private} |"
        f"is_verified_Used={ds.is_verified_used}",
        "bold",
    )
    received_deposit, *_ = ebb.getStorageInfo(provider, requester, code_hash)
    log(f"received_deposit={received_deposit}", "bold")


def test_submit_n_data():
    gas_costs = []
    job = Job()
    provider = accounts[1]
    requester = accounts[2]
    price_core_min = Cent("100 cent")
    register_provider(price_core_min, available_core=128)
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
    provider_price_bn = ebb.getProviderSetBlockNumbers(provider)[-1]
    args = [
        provider,
        provider_price_bn,
        job.storage_ids,
        job.cache_types,
        job.data_prices_set_block_numbers,
        job.cores,
        job.run_time,
        job.data_transfer_out,
        job_price,
    ]
    _transfer(requester, Cent(job_price))
    tx = ebb.submitJob(
        job.key,
        job.data_transfer_ins,
        args,
        job.storage_hours,
        job.code_hashes,
        {"from": requester},
    )
    gas_costs.append(tx.__dict__["gas_used"])
    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    job.code_hashes = [b"9b3e9babb6539c1aceea8d606fc55403", b"9a4c0c1c9aadb203daf9367bd4df930b"]
    job.key = job.code_hashes[0]
    job.cores = [2]
    job.run_time = [1]
    job.data_transfer_ins = [1, 1]
    job.data_transfer_out = 1
    job.storage_ids = [StorageID.B2DROP.value, StorageID.B2DROP.value]
    job.cache_types = [CacheType.PUBLIC.value, CacheType.PUBLIC.value]
    job.storage_hours = [0, 0]
    job.data_prices_set_block_numbers = [0, 0]
    job_price, *_ = job.cost(provider, requester)
    provider_price_bn = ebb.getProviderSetBlockNumbers(provider)[-1]
    args = [
        provider,
        provider_price_bn,
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
    provider_price_bn = ebb.getProviderSetBlockNumbers(provider)[-1]
    args = [
        provider,
        provider_price_bn,
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
    gas_costs.append(tx.__dict__["gas_used"])

    # new job submission
    # -=-=-=-=-=-=-=-=-=
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
    provider_price_bn = ebb.getProviderSetBlockNumbers(provider)[-1]
    args = [
        provider,
        provider_price_bn,
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
    gas_costs.append(tx.__dict__["gas_used"])
    log("#> submit_job data number gas differences:")
    print(gas_costs)
    for idx in range(0, 3):
        print(gas_costs[idx + 1] - gas_costs[idx])


def test_receive_registered_data_deposit():
    provider = accounts[1]
    requester = accounts[2]
    a_core = 128
    register_provider(available_core=a_core)
    register_requester(requester)

    data_hash = "0x68b8d8218e730fc2957bcb12119cb204"
    ebb.registerData(data_hash, 10, cfg.ONE_HOUR_BLOCK_DURATION, {"from": provider})
    data_prices = ebb.getRegisteredDataPrice(provider, data_hash, 0)
    assert data_prices[0] == 10
    mine(1)
    data_hash_2 = "0x68b8d8218e730fc2957bcb12119cb205"
    ebb.registerData(data_hash_2, 20, cfg.ONE_HOUR_BLOCK_DURATION, {"from": provider})
    data_prices = ebb.getRegisteredDataPrice(provider, data_hash_2, 0)
    assert data_prices[0] == 20
    mine(1)

    job = Job()
    # job_key = "QmQv4AAL8DZNxZeK3jfJGJi63v1msLMZGan7vSsCDXzZud"
    # job.code_hashes.append(ipfs_to_bytes32(job_key))
    # job.code_hashes.append(ipfs_to_bytes32("QmVqtWxuBdZQdLnLce6XCBMuqoazAcbmuxoJHQbfbuqDu2"))
    job.code_hashes = [b"9b3e9babb6539c1aceea8d606fc55403", data_hash, data_hash_2]
    job.key = job.code_hashes[0]
    job.cores = [1]
    job.run_time = [1]
    job.data_transfer_ins = [1, 0, 0]
    job.data_transfer_out = 0
    job.storage_ids = [StorageID.B2DROP.value, StorageID.NONE.value, StorageID.NONE.value]
    job.cache_types = [CacheType.PUBLIC.value, CacheType.PUBLIC.value, CacheType.PUBLIC.value]
    job.storage_hours = [0, 0, 0]
    job.data_prices_set_block_numbers = [0, 0, 0]
    job.provider_price_bn = ebb.getProviderSetBlockNumbers(provider)[-1]
    job_price, *_ = job.cost(provider, requester)
    args = [
        provider,
        job.provider_price_bn,
        job.storage_ids,
        job.cache_types,
        job.data_prices_set_block_numbers,
        job.cores,
        job.run_time,
        job.data_transfer_out,
        job_price,
    ]
    # print(job_price)
    _transfer(requester, Cent(job_price))
    tx = ebb.submitJob(
        job.key,
        job.data_transfer_ins,
        args,
        job.storage_hours,
        job.code_hashes,
        {"from": requester},
    )
    #
    start_ts = get_block_timestamp()
    index = 0
    received = tx.events["LogJob"]["received"]
    # log(f"job_received={received}")
    _recieved = ebb.getJobInfo(provider, job.key, index, 0)[1]
    assert received == _recieved
    # log(_recieved)
    tx = ebb.setJobStateRunning(job.key, index, job._id, start_ts, {"from": provider})
    rpc.sleep(60)
    mine(10)
    elapsed_time = job.run_time[0]
    end_ts = start_ts + 60 * elapsed_time
    #
    data_transfer_in_sum = 1
    data_transfer_out = 0
    args = [index, job._id, end_ts, data_transfer_in_sum, data_transfer_out, elapsed_time, job.cores, [1]]
    tx = ebb.processPayment(job.key, args, "", {"from": provider})
    received = tx.events["LogProcessPayment"]["receivedCent"]
    refunded = tx.events["LogProcessPayment"]["refundedCent"]
    log(f"received={received} refunded={refunded}")
    assert job_price == received + refunded


def report():
    """Cleanup a testing directory once we are finished.

    __ https://stackoverflow.com/a/51025279/2402577"""
    print_gas_costs()  #


atexit.register(report)
