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


def test_workflow_1():
    # [42, 62, 77, 3, 76, 14, 1, 48, 17, 15, 51, 86, 94, 26, 91, 57]
    provider = accounts[1]
    requester = accounts[2]
    register_provider(available_core=4, prices=prices)
    register_requester(requester)
    job_key = "QmQv4AAL8DZNxZeK3jfJGJi63v1msLMZGan7vSsCDXzZud"
    code_hash = ipfs_to_bytes32(job_key)
    job = Job()
    job.code_hashes = [code_hash]
    job.storage_hours = [0]
    job.data_transfer_ins = [200]
    job.data_transfer_out = 984
    job.data_prices_set_block_numbers = [0]
    job.cores = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    job.run_time = [4, 5, 2, 5, 3, 3, 3, 2, 4, 5, 4, 5, 2, 5, 3]
    job.storage_ids = [StorageID.IPFS.value]
    job.cache_types = [CacheID.PUBLIC.value]
    job_price, cost = job.cost(provider, requester, is_verbose=True)
    workflow_id = 0
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
        workflow_id,
    ]
    _transfer(requester, Cent(job_price))
    log(f"job_price={float(Cent(job_price).to('usd'))} usd")
    ebb.submitJob(
        job_key,
        job.data_transfer_ins,
        args,
        job.storage_hours,
        job.code_hashes,
        {"from": requester},
    )
    start_timestamp = 10
    for idx in range(0, 5):
        ebb.setJobStateRunning(job_key, 0, idx, start_timestamp, {"from": provider})

    # process_payment for the workflow
    index = 0
    job_id = 0
    elapsed_time = 4
    data_transfer = [0, 22]
    ended_timestamp = 10 + elapsed_time * 60
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
        JOB.TYPE["FINAL"],
    ]
    ebb.processPayment(job_key, args, result_ipfs_hash, {"from": provider})
    # ----------------------------------------------------------------------------------g
    index = 0
    job_id = 0
    elapsed_time = 4
    data_transfer = [0, 22]
    ended_timestamp = 10 + elapsed_time * 60
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
        JOB.TYPE["BEGIN"],
    ]
    ebb.processPayment(job_key, args, result_ipfs_hash, {"from": provider})
    # ----------------------------------------------------------------------------------g
    index = 0
    job_id = 2
    elapsed_time = 2
    data_transfer = [0, 20]
    ended_timestamp = 10 + elapsed_time * 60
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
        JOB.TYPE["BETWEEN"],
    ]
    ebb.processPayment(job_key, args, result_ipfs_hash, {"from": provider})
    # ----------------------------------------------------------------------------------g
    index = 0
    job_id = 3
    elapsed_time = 2
    data_transfer = [0, 20]
    ended_timestamp = 10 + elapsed_time * 60
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
        JOB.TYPE["BETWEEN"],
    ]
    ebb.processPayment(job_key, args, result_ipfs_hash, {"from": provider})

    # breakpoint()  # DEBUG


def test_workflow_2():
    job = Job()
    provider = accounts[1]
    requester = accounts[2]
    register_provider(available_core=128)
    register_requester(requester)
    job_key = "QmQv4AAL8DZNxZeK3jfJGJi63v1msLMZGan7vSsCDXzZud"
    code_hash = ipfs_to_bytes32(job_key)
    with brownie.reverts():
        ebb.updataDataPrice(code_hash, Cent("2 cent"), 100, {"from": provider})

    tx = ebb.registerData(code_hash, Cent("2 cent"), cfg.ONE_HOUR_BLOCK_DURATION, {"from": provider})
    append_gas_cost("registerData", tx)
    ebb.removeRegisteredData(code_hash, {"from": provider})  # submitJob() should fail if it is not removed
    append_gas_cost("removeRegisteredData", tx)
    data_hash = "0x68b8d8218e730fc2957bcb12119cb204"
    ebb.registerData(data_hash, Cent("2 cent"), cfg.ONE_HOUR_BLOCK_DURATION, {"from": provider})
    append_gas_cost("registerData", tx)
    mine(6)
    with brownie.reverts():
        ebb.registerData(data_hash, Cent("3 cent"), 1000, {"from": provider})

    tx = ebb.updataDataPrice(data_hash, Cent("25 cent"), cfg.ONE_HOUR_BLOCK_DURATION, {"from": provider})
    append_gas_cost("updataDataPrice", tx)
    tx = ebb.updataDataPrice(data_hash, Cent("26 cent"), cfg.ONE_HOUR_BLOCK_DURATION + 1, {"from": provider})
    append_gas_cost("updataDataPrice", tx)
    data_block_numbers = ebb.getRegisteredDataBlockNumbers(provider, data_hash)
    log(f"get_registered_data_block_numbers={data_block_numbers[1]}")
    get_bn()
    data_prices = ebb.getRegisteredDataPrice(provider, data_hash, 0)
    assert data_prices[0] == Cent("2 cent")
    output = ebb.getRegisteredDataPrice(provider, data_hash, data_block_numbers[-1])
    assert output[0] == Cent("26 cent")
    mine(cfg.ONE_HOUR_BLOCK_DURATION - 10)
    output = ebb.getRegisteredDataPrice(provider, data_hash, 0)
    log(f"register_data_price={output}")
    assert output[0] == Cent("2 cent")
    mine(1)
    output = ebb.getRegisteredDataPrice(provider, data_hash, 0)
    log(f"register_data_price={output}")
    assert output[0] == Cent("26 cent")

    job.code_hashes = [code_hash, data_hash]  # Hashed of the data file in array
    job.storage_hours = [0, 0]
    job.data_transfer_ins = [100, 0]
    job.data_transfer_out = 100

    # job.data_prices_set_block_numbers = [0, 253]  # TODO: check this ex 253 exists or not
    job.data_prices_set_block_numbers = [0, data_block_numbers[1]]  # TODO: check this ex 253 exists or not
    check_price_keys(job.data_prices_set_block_numbers, provider, data_hash)
    job.cores = [1, 1, 1]
    job.run_time = [10, 15, 20]
    job.storage_ids = [StorageID.IPFS.value, StorageID.NONE.value]
    job.cache_types = [CacheID.PUBLIC.value, CacheID.PUBLIC.value]
    job_price, cost = job.cost(provider, requester)
    workflow_id = 0
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
        workflow_id,
    ]
    _transfer(requester, Cent(job_price))
    tx = ebb.submitJob(  # first job submit
        job_key,
        job.data_transfer_ins,
        args,
        job.storage_hours,
        job.code_hashes,
        {"from": requester},
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
    tx = ebb.setJobStateRunning(job_key, index, job_id, start_timestamp, {"from": provider})
    append_gas_cost("setJobStateRunning", tx)
    index = 0
    job_id = 1
    start_timestamp = 20
    tx = ebb.setJobStateRunning(job_key, index, job_id, start_timestamp, {"from": provider})
    append_gas_cost("setJobStateRunning", tx)
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
        JOB.TYPE["BEGIN"],
    ]
    # print_gas_costs() #
    tx = ebb.processPayment(job_key, args, result_ipfs_hash, {"from": provider})
    append_gas_cost("processPayment", tx)
    # log(tx.events['LogProcessPayment'])
    received_sums.append(tx.events["LogProcessPayment"]["receivedCent"])
    refunded_sums.append(tx.events["LogProcessPayment"]["refundedCent"])
    received_sum += tx.events["LogProcessPayment"]["receivedCent"]
    refunded_sum += tx.events["LogProcessPayment"]["refundedCent"]
    log(f"received_sum={received_sum} | refunded_sum={refunded_sum}")
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
        JOB.TYPE["BETWEEN"],
    ]
    tx = ebb.processPayment(job_key, args, result_ipfs_hash, {"from": provider})
    assert tx.events["LogProcessPayment"]["elapsedTime"] == elapsed_time
    append_gas_cost("processPayment", tx)
    received_sums.append(tx.events["LogProcessPayment"]["receivedCent"])
    refunded_sums.append(tx.events["LogProcessPayment"]["refundedCent"])
    received_sum += tx.events["LogProcessPayment"]["receivedCent"]
    refunded_sum += tx.events["LogProcessPayment"]["refundedCent"]
    log(f"received_sum={received_sum} | refunded_sum={refunded_sum}")
    assert refunded_sum == 0
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
            JOB.TYPE["BETWEEN"],
        ]
        tx = ebb.processPayment(job_key, args, result_ipfs_hash, {"from": provider})
        append_gas_cost("processPayment", tx)

    index = 0
    job_id = 2
    start_timestamp = 20
    tx = ebb.setJobStateRunning(job_key, index, job_id, start_timestamp, {"from": provider})
    append_gas_cost("setJobStateRunning", tx)
    args = [
        index,
        job_id,
        ended_timestamp,
        data_transfer[0],
        data_transfer[1],
        elapsed_time,
        job.cores,
        job.run_time,
        JOB.TYPE["FINAL"],
    ]
    tx = ebb.processPayment(job_key, args, result_ipfs_hash, {"from": provider})
    assert tx.events["LogProcessPayment"]["elapsedTime"] == elapsed_time
    append_gas_cost("processPayment", tx)
    received_sums.append(tx.events["LogProcessPayment"]["receivedCent"])
    refunded_sums.append(tx.events["LogProcessPayment"]["refundedCent"])
    received_sum += tx.events["LogProcessPayment"]["receivedCent"]
    refunded_sum += tx.events["LogProcessPayment"]["refundedCent"]
    _refunded_sum = Cent(refunded_sum).to_usd()
    _received_sum = Cent(received_sum).to_usd()
    job_price_str = Cent(job_price).to_usd()
    log(f"==> received_sum={_received_sum} usd | refunded_sum={_refunded_sum} usd | job_price={job_price_str} usd")
    log(f"==> received_sums={received_sums}")
    log(f"==> refunded_sums={refunded_sums}")
    assert _refunded_sum == 0
    _cfg.TOKEN.transferFrom(ebb.address, requester, _cfg.TOKEN.allowance(ebb.address, requester), {"from": requester})
    _cfg.TOKEN.transferFrom(ebb.address, provider, _cfg.TOKEN.allowance(ebb.address, provider), {"from": provider})
    assert _cfg.TOKEN.balanceOf(provider) == received_sum
    assert _cfg.TOKEN.balanceOf(requester) == refunded_sum
    assert job_price == received_sum + refunded_sum


def test_workflow_3():
    provider = accounts[1]
    requester = accounts[2]
    register_provider(available_core=4, prices=prices)
    register_requester(requester)
    job_key = "QmQv4AAL8DZNxZeK3jfJGJi63v1msLMZGan7vSsCDXzZud"
    data_hash = "QmQv4AAL8DZNxZeK3jfJGJi63v1msLMZGan7vSsCDXzZum"

    code_hash = ipfs_to_bytes32(job_key)
    data_hash = ipfs_to_bytes32(data_hash)

    job = Job()
    job.code_hashes = [code_hash, data_hash]
    job.storage_hours = [0, 0]
    job.data_transfer_ins = [150, 100]
    job.data_transfer_out = 10
    job.data_prices_set_block_numbers = [0, 0]
    job.cores = [1, 1, 1, 1, 1]
    job.run_time = [100, 100, 50, 50, 50]
    job.storage_ids = [StorageID.IPFS.value, StorageID.IPFS.value]
    job.cache_types = [CacheID.PUBLIC.value, CacheID.PUBLIC.value]
    job_price, cost = job.cost(provider, requester, is_verbose=True)
    workflow_id = 0
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
        workflow_id,
    ]
    _transfer(requester, Cent(job_price))
    # TODO: datatransferout considered 2x
    log(f"job_price={float(Cent(job_price).to('usd'))} usd")
    tx = ebb.submitJob(  # first job submit
        job_key,
        job.data_transfer_ins,
        args,
        job.storage_hours,
        job.code_hashes,
        {"from": requester},
    )
    for idx in range(0, 5):
        log(ebb.getJobInfo(provider, job_key, 0, idx))

    # console_ruler(character="-=")
    # assert (
    #     tx.events["LogRegisteredDataRequestToUse"][0]["registeredDataHash"]
    #     == "0x0000000000000000000000000000000068b8d8218e730fc2957bcb12119cb204"
    # ), "registered data should be used"

    # with brownie.reverts():
    #     log(ebb.getJobInfo(provider, job_key, 1, 2))
    #     log(ebb.getJobInfo(provider, job_key, 0, 3))

    # # setJobState for the workflow:
    # index = 0
    # job_id = 0
    # start_timestamp = 10
    # tx = ebb.setJobStateRunning(job_key, index, job_id, start_timestamp, {"from": provider})
    # append_gas_cost("setJobStateRunning", tx)
    # index = 0
    # job_id = 1
    # start_timestamp = 20
    # tx = ebb.setJobStateRunning(job_key, index, job_id, start_timestamp, {"from": provider})
    # append_gas_cost("setJobStateRunning", tx)
    # # process_payment for the workflow
    # index = 0
    # job_id = 0
    # elapsed_time = 10
    # data_transfer = [100, 0]
    # ended_timestamp = 20
    # result_ipfs_hash = ipfs_to_bytes32("QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Ve")
    # received_sums = []
    # refunded_sums = []
    # received_sum = 0
    # refunded_sum = 0
    # args = [
    #     index,
    #     job_id,
    #     ended_timestamp,
    #     data_transfer[0],
    #     data_transfer[1],
    #     elapsed_time,
    #     job.cores,
    #     job.run_time,
    #     JOB.TYPE["BEGIN"],
    # ]
    # # print_gas_costs() #
    # tx = ebb.processPayment(job_key, args, result_ipfs_hash, {"from": provider})
    # append_gas_cost("processPayment", tx)
    # # log(tx.events['LogProcessPayment'])
    # received_sums.append(tx.events["LogProcessPayment"]["receivedCent"])
    # refunded_sums.append(tx.events["LogProcessPayment"]["refundedCent"])
    # received_sum += tx.events["LogProcessPayment"]["receivedCent"]
    # refunded_sum += tx.events["LogProcessPayment"]["refundedCent"]
    # log(f"received_sum={received_sum} | refunded_sum={refunded_sum}")
    # index = 0
    # job_id = 1
    # elapsed_time = 15
    # data_transfer = [0, 0]
    # ended_timestamp = 39
    # result_ipfs_hash = ipfs_to_bytes32("QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Ve")
    # args = [
    #     index,
    #     job_id,
    #     ended_timestamp,
    #     data_transfer[0],
    #     data_transfer[1],
    #     elapsed_time,
    #     job.cores,
    #     job.run_time,
    #     JOB.TYPE["BETWEEN"],
    # ]
    # tx = ebb.processPayment(job_key, args, result_ipfs_hash, {"from": provider})
    # assert tx.events["LogProcessPayment"]["elapsedTime"] == elapsed_time
    # append_gas_cost("processPayment", tx)
    # received_sums.append(tx.events["LogProcessPayment"]["receivedCent"])
    # refunded_sums.append(tx.events["LogProcessPayment"]["refundedCent"])
    # received_sum += tx.events["LogProcessPayment"]["receivedCent"]
    # refunded_sum += tx.events["LogProcessPayment"]["refundedCent"]
    # log(f"received_sum={received_sum} | refunded_sum={refunded_sum}")
    # assert refunded_sum == 0
    # index = 0
    # job_id = 2
    # elapsed_time = 20
    # data_transfer = [0, 100]
    # ended_timestamp = 39
    # result_ipfs_hash = ipfs_to_bytes32("QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Ve")
    # with brownie.reverts():  # processPayment should revert, setRunning is not called for the job=2
    #     args = [
    #         index,
    #         job_id,
    #         ended_timestamp,
    #         data_transfer[0],
    #         data_transfer[1],
    #         elapsed_time,
    #         job.cores,
    #         job.run_time,
    #         JOB.TYPE["BETWEEN"],
    #     ]
    #     tx = ebb.processPayment(job_key, args, result_ipfs_hash, {"from": provider})
    #     append_gas_cost("processPayment", tx)

    # index = 0
    # job_id = 2
    # start_timestamp = 20
    # tx = ebb.setJobStateRunning(job_key, index, job_id, start_timestamp, {"from": provider})
    # append_gas_cost("setJobStateRunning", tx)
    # args = [
    #     index,
    #     job_id,
    #     ended_timestamp,
    #     data_transfer[0],
    #     data_transfer[1],
    #     elapsed_time,
    #     job.cores,
    #     job.run_time,
    #     JOB.TYPE["FINAL"],
    # ]
    # tx = ebb.processPayment(job_key, args, result_ipfs_hash, {"from": provider})
    # assert tx.events["LogProcessPayment"]["elapsedTime"] == elapsed_time
    # append_gas_cost("processPayment", tx)
    # received_sums.append(tx.events["LogProcessPayment"]["receivedCent"])
    # refunded_sums.append(tx.events["LogProcessPayment"]["refundedCent"])
    # received_sum += tx.events["LogProcessPayment"]["receivedCent"]
    # refunded_sum += tx.events["LogProcessPayment"]["refundedCent"]
    # _refunded_sum = Cent(refunded_sum).to_usd()
    # _received_sum = Cent(received_sum).to_usd()
    # job_price_str = Cent(job_price).to_usd()
    # log(f"==> received_sum={_received_sum} usd | refunded_sum={_refunded_sum} usd | job_price={job_price_str} usd")
    # log(f"==> received_sums={received_sums}")
    # log(f"==> refunded_sums={refunded_sums}")
    # assert _refunded_sum == 0
    # _cfg.TOKEN.transferFrom(ebb.address, requester, _cfg.TOKEN.allowance(ebb.address, requester), {"from": requester})
    # _cfg.TOKEN.transferFrom(ebb.address, provider, _cfg.TOKEN.allowance(ebb.address, provider), {"from": provider})
    # assert _cfg.TOKEN.balanceOf(provider) == received_sum
    # assert _cfg.TOKEN.balanceOf(requester) == refunded_sum
    # assert job_price == received_sum + refunded_sum
