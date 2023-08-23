#!/usr/bin/python3

from broker._utils.yaml import Yaml
from pathlib import Path
import os
import pytest
import sys
from os import path
from broker.workflow.Workflow import Workflow
import contract.tests.cfg as _cfg
from broker import cfg, config
from broker.config import setup_logger
from broker.eblocbroker_scripts import Contract
from broker.eblocbroker_scripts.job import Job
from broker.eblocbroker_scripts.utils import Cent
from broker.utils import CacheID, StorageID, ipfs_to_bytes32, log
from brownie import accounts, web3
from brownie.network.state import Chain
from contract.scripts.lib import gas_costs, new_test
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
    log(f"bn={web3.eth.blockNumber} | contract_bn={web3.eth.blockNumber + 1}")
    return web3.eth.blockNumber


def get_block_timestamp():
    return web3.eth.getBlock(get_bn()).timestamp


@pytest.mark.skip(reason="no way of currently testing this")
def test_dummy():
    pass


def calculate_cost(provider, requester, item, workflow_id, estimated_elapse_time, wf):
    job = Job()
    job_key = "QmQv4AAL8DZNxZeK3jfJGJi63v1msLMZGan7vSsCDXzZud"
    code_hash = ipfs_to_bytes32(job_key)
    job.code_hashes = [code_hash]
    job.cores = []
    job.run_time = []
    job.data_transfer_ins = []
    job.storage_hours = [0]
    job.data_transfer_ins = [1000]
    job.data_transfer_out = 0
    job.data_prices_set_block_numbers = [0]
    job.storage_ids = [StorageID.IPFS.value]
    job.cache_types = [CacheID.PUBLIC.value]
    _item = [int(x) for x in item]
    _item.sort()
    for _id in _item:
        job.cores.append(1)
        # job.data_transfer_ins.append(code_size[_id])
        job.run_time.append(estimated_elapse_time[_id])

        #: https://stackoverflow.com/a/62100191/2402577
        for _, v, w in wf.G.edges(str(_id), data=True):
            # print(u, v, w["weight"])
            if int(v) not in _item:
                job.data_transfer_out += int(w["weight"])

    job_price, cost = job.cost(provider, requester, is_verbose=True)
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
    tx = ebb.submitJob(  # first job submit
        job_key,
        job.data_transfer_ins,
        args,
        job.storage_hours,
        job.code_hashes,
        {"from": requester},
    )
    # for idx in range(0, len(job.cores)):
    #     log(ebb.getJobInfo(provider, job_key, 0, idx))
    # breakpoint()  # DEBUG


def test_workflow():
    yaml_fn = Path.home() / "ebloc-broker" / "contract" / "jobs.yaml"
    yaml = Yaml(yaml_fn)
    #
    provider = accounts[1]
    requester = accounts[2]
    register_provider(available_core=128, prices=prices)
    register_requester(requester)

    wf = Workflow()
    wf.read_dot("workflow_job.dot")

    log(wf.topological_sort())
    log(wf.topological_generations())

    estimated_elapse_time = {}
    code_size = {}
    # number_of_nodes = wf.number_of_nodes()
    for idx, item in enumerate(yaml["jobs"]):
        estimated_elapse_time[idx] = yaml["jobs"][item]["run_time"]
        code_size[idx] = yaml["jobs"][item]["size"]

    layer_list = []
    inner_layer = []
    flag_est_time = 0
    thresehold = 120
    for idx, item in enumerate(wf.topological_generations()):
        if "\\n" in item:
            item.remove("\\n")

        max_est_time = 0
        for job in item:
            if estimated_elapse_time[int(job)] > max_est_time:
                max_est_time = estimated_elapse_time[int(job)]

        flag_est_time += max_est_time
        if flag_est_time <= thresehold:
            for job in item:
                inner_layer.append(job)
        else:
            layer_list.append(inner_layer)
            flag_est_time = max_est_time
            inner_layer = []
            for job in item:
                inner_layer.append(job)

    # for idx, item in enumerate(wf.topological_generations()):
    for idx, item in enumerate(layer_list):
        if "\\n" in item:
            item.remove("\\n")

        print(item)
        workflow_id = idx
        #: calculate the cost for each layer
        calculate_cost(provider, requester, item, workflow_id, estimated_elapse_time, wf)
