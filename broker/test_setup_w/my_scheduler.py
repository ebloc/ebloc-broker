#!/usr/bin/env python3

import time
from broker.lib import state
from typing import List
from contextlib import suppress
import networkx as nx
from broker._utils.yaml import Yaml
from pathlib import Path
from broker._utils.tools import print_tb
from broker.errors import QuietExit
from heft.core import schedule
from broker.workflow.Workflow import Workflow
from broker._utils._log import log
from broker.eblocbroker_scripts.job import Job
from broker.ipfs.submit import submit_ipfs
from broker import cfg
from broker.eblocbroker_scripts import Contract


BASE = Path.home() / "test_eblocbroker" / "test_data" / "base" / "source_code_wf_random"
wf = Workflow()
yaml_fn = Path.home() / "test_eblocbroker" / "test_data" / "base" / "source_code_wf_random" / "jobs.yaml"
yaml_fn_wf = Path.home() / "ebloc-broker" / "broker" / "test_setup_w" / "job_workflow.yaml"
yaml = Yaml(yaml_fn)

provider_id = {}
provider_id["a"] = "0x29e613B04125c16db3f3613563bFdd0BA24Cb629"
provider_id["b"] = "0x4934a70Ba8c1C3aCFA72E809118BDd9048563A24"
provider_id["c"] = "0xe2e146d6B456760150d78819af7d276a1223A6d4"

Ebb: "Contract.Contract" = cfg.Ebb


def computation_cost(job, agent):
    return yaml["config"]["jobs"][f"job{job}"]["costs"][provider_id[agent]]


def communication_cost(ni, nj, A, B):
    if A == B:
        return 0
    else:
        return wf.get_weight(ni, nj)


class Ewe:
    def __init__(self) -> None:
        self.slots = {}  # type: ignore
        self.batch_to_submit = {}  # type: ignore
        #
        self.ready: List[int] = []
        self.submitted_dict = {}
        self.submitted: List[int] = []
        self.running: List[int] = []
        self.completed: List[int] = []
        self.remaining: List[int] = []

    def set_batch_to_submit(self) -> None:
        self.batch_to_submit = {}
        for key, value in self.slots.items():
            for v in value:
                dependent_jobs = wf.in_edges(v)
                flag = False
                if dependent_jobs:
                    for dependent_job in dependent_jobs:
                        if dependent_job not in self.slots[key]:
                            flag = True
                            break

                if not flag:
                    if key not in self.batch_to_submit:
                        self.batch_to_submit[key] = []

                    self.batch_to_submit[key].append(v)

    def set_batch_to_submit_in_while(self) -> None:
        self.batch_to_submit = {}
        for key, value in self.slots.items():
            for v in value:
                if v in self.ready:  # 5, 3, 4
                    dependent_jobs = wf.in_edges(v)  # 4 1 2
                    with suppress(Exception):
                        dependent_jobs = list(set(dependent_jobs) - set(self.batch_to_submit[key]))

                    flag = False
                    for dependent_job in dependent_jobs:
                        if dependent_job not in self.completed:
                            flag = True
                            break

                    if not flag:
                        log(f"job: {v} is ready to submit")
                        if key not in self.batch_to_submit:
                            self.batch_to_submit[key] = []

                        self.batch_to_submit[key].append(v)
                        breakpoint()  # DEBUG

    def batch_submit(self):
        for batch_key in self.batch_to_submit:
            G_copy = wf.G.copy()
            yaml_cfg = Yaml(yaml_fn_wf)
            yaml_cfg["config"]["provider_address"] = provider_id[batch_key]
            g_list = []
            for node in list(wf.G.nodes):
                if node != "\\n" and int(node) not in self.batch_to_submit[batch_key]:
                    g_list.append(node)

            with suppress(Exception):
                G_copy.remove_node("\\n")

            for key in g_list:
                G_copy.remove_node(key)

            nx.nx_pydot.write_dot(G_copy, BASE / "sub_workflow_job.dot")
            if len(self.batch_to_submit[batch_key]) == 1:
                node = self.batch_to_submit[batch_key][0]
                yaml_cfg["config"]["jobs"] = {}
                yaml_cfg["config"]["jobs"][f"job{node}"]["cores"] = 1
                yaml_cfg["config"]["jobs"][f"job{node}"]["run_time"] = yaml["config"]["jobs"][f"job{node}"]["run_time"]
                yaml_cfg["config"]["dt_in"] = yaml["config"]["jobs"][f"job{node}"]["dt_in"]
                yaml_cfg["config"]["data_transfer_out"] = yaml["config"]["jobs"][f"job{node}"]["dt_out"]
            elif self.batch_to_submit[batch_key]:
                sink_nodes = []
                for node in list(G_copy.nodes):
                    in_edges = G_copy.in_edges(node)
                    # print(f"{node} => {in_edges}")
                    if not in_edges:
                        sink_nodes.append(node)

                yaml_cfg["config"]["jobs"] = {}
                yaml_cfg["config"]["dt_in"] = 200
                yaml_cfg["config"]["data_transfer_out"] = 0
                #: should start from the first job
                for node in list(G_copy.nodes):
                    yaml_cfg["config"]["jobs"][f"job{node}"]["cores"] = 1
                    yaml_cfg["config"]["jobs"][f"job{node}"]["run_time"] = yaml["config"]["jobs"][f"job{node}"][
                        "run_time"
                    ]
                    yaml_cfg["config"]["data_transfer_out"] += yaml["config"]["jobs"][f"job{node}"]["dt_out"]
                    if node in sink_nodes:
                        yaml_cfg["config"]["dt_in"] += yaml["config"]["jobs"][f"job{node}"]["dt_in"] - 200

                #: subtract inner edge weight from dt_out since its in the same graph
                for u, v, d in G_copy.edges(data=True):
                    yaml_cfg["config"]["data_transfer_out"] -= int(d["weight"])
                    # print(u, v, d)

            job = Job()
            job.set_config(yaml_fn_wf)
            submit_ipfs(job)  # submits the job
            key = f"{job.info['provider']}_{job.info['jobKey']}_{job.info['index']}_{job.info['blockNumber']}"

            for node in list(G_copy.nodes):
                if node != "\\n":
                    try:
                        self.submitted_dict[key].append(int(node))
                    except:
                        self.submitted_dict[key] = [int(node)]

            for node in list(G_copy.nodes):
                self.ready.remove(int(node))
                self.submitted.append(int(node))
            # else:
            #     breakpoint()  # DEBUG


def check_jobs(ewe):
    print(f"READY     => {ewe.ready}")
    print(f"SUBMITTED => {ewe.submitted}")
    print(f"RUNNING   => {ewe.running}")
    print(f"COMPLETED => {ewe.completed}")
    print("-----------------------------------")
    for key, value in ewe.submitted_dict.items():
        for idx, val in enumerate(sorted(value)):
            keys = key.split("_")
            _job = Ebb.get_job_info(keys[0], keys[1], keys[2], idx, keys[3], is_print=True)
            state_val = state.inv_code[_job["stateCode"]]
            if state_val == "SUBMITTED":
                pass
            if state_val == "RUNNING":
                if val in ewe.submitted:
                    log(f"==> state changed to RUNNING for job: {val}")
                    ewe.submitted.remove(val)
                    ewe.running.append(val)
            if state_val == "COMPLETED":
                if val in ewe.submitted or val in ewe.running:
                    log(f"==> state changed to COMPLETED for job: {val}")
                    with suppress(Exception):
                        ewe.submitted.remove(val)

                    with suppress(Exception):
                        ewe.running.remove(val)

                    ewe.completed.append(val)
                    ewe.set_batch_to_submit_in_while()
                    if ewe.batch_to_submit:
                        log(ewe.batch_to_submit)
                        breakpoint()  # DEBUG
                        ewe.batch_submit()
                        return

                    # TODO: recursive check to submit new jobs


def main():
    ewe = Ewe()
    slots = {}
    fn = "/home/alper/test_eblocbroker/test_data/base/source_code_wf_random/workflow_job.dot"
    wf.read_dot(fn)
    # wf.read_dot("job.dot")
    dag = wf.dot_to_tuple()
    orders, jobson = schedule(dag, "abc", computation_cost, communication_cost)
    for key, _ in provider_id.items():
        for order in orders[key]:
            if key not in slots:
                slots[key] = [int(order.job)]
            else:
                slots[key].append(int(order.job))

    log(slots)
    ewe.slots = slots
    for node in list(wf.G_sorted()):
        ewe.ready.append(int(node))

    ewe.set_batch_to_submit()
    log(ewe.batch_to_submit)
    ewe.batch_submit()
    while True:
        check_jobs(ewe)
        time.sleep(2)
        # submit job

    ##########################################################################################
    # for job in batch_to_submit:
    #     submitted_jobs.append(job)

    # breakpoint()  # DEBUG
    # for order in sorted(orders):
    #     print(order, orders[order])

    # dependent_jobs = wf.in_edges(9)
    log(jobson)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except QuietExit as e:
        print(f"#> {e}")
    except Exception as e:
        print_tb(str(e))

"""
This is a simple script to use the HEFT function provided based on the example given in the original HEFT paper.
You have to define the DAG, computation_cost function and communication_cost funtion.

Each task/job is numbered 1 to 10
Each processor/agent is named 'a', 'b' and 'c'

Output expected:
Ranking:
[10, 8, 7, 9, 6, 5, 2, 4, 3, 1]
Schedule:
('a', [Event(job=2, start=27, end=40), Event(job=8, start=57, end=62)])
('b', [Event(job=4, start=18, end=26), Event(job=6, start=26, end=42), Event(job=9, start=56, end=68), Event(job=10, start=73, end=80)])
('c', [Event(job=1, start=0, end=9), Event(job=3, start=9, end=28), Event(job=5, start=28, end=38), Event(job=7, start=38, end=49)])
{1: 'c', 2: 'a', 3: 'c', 4: 'b', 5: 'c', 6: 'b', 7: 'c', 8: 'a', 9: 'b', 10: 'b'}
"""
