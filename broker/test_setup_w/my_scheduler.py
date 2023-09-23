#!/usr/bin/env python3

import sys
import datetime
import networkx as nx
import pickle
import time
from contextlib import suppress
from heft.core import schedule
from pathlib import Path
from timeit import default_timer
from typing import Dict, List

from broker import cfg
from broker._utils._log import log
from broker._utils.tools import print_tb
from broker._utils.yaml import Yaml
from broker.eblocbroker_scripts import Contract
from broker.eblocbroker_scripts.job import Job
from broker.errors import QuietExit
from broker.ipfs.submit import submit_ipfs
from broker.lib import state
from broker.workflow.Workflow import Workflow

wf = Workflow()

if len(sys.argv) == 3:
    n = int(sys.argv[1])
    edges = int(sys.argv[2])
else:
    n = 10
    edges = 10

BASE = Path.home() / "test_eblocbroker" / "workflow" / f"{n}_{edges}"
# BASE = Path.home() / "test_eblocbroker" / "test_data" / "base" / "source_code_wf_random"
yaml_fn = BASE / "jobs.yaml"
#: dummy file updated anyway
yaml_fn_wf = Path.home() / "ebloc-broker" / "broker" / "test_setup_w" / "job_workflow.yaml"
yaml = Yaml(yaml_fn)

slots = {}  # type: ignore
provider_id = {}
provider_id["a"] = "0x29e613B04125c16db3f3613563bFdd0BA24Cb629"
provider_id["b"] = "0x4934a70Ba8c1C3aCFA72E809118BDd9048563A24"
provider_id["c"] = "0xe2e146d6B456760150d78819af7d276a1223A6d4"

try:
    with open(BASE / "heft_submitted_dict.pkl", "rb") as f:
        loaded_dict = pickle.load(f)
except:
    pass


Ebb: "Contract.Contract" = cfg.Ebb


def computation_cost(job, agent):
    return yaml["config"]["jobs"][f"job{job}"]["costs"][provider_id[agent]]


def communication_cost(ni, nj, A, B):
    if A == B:
        return 0

    return wf.get_weight(ni, nj)


class Ewe:
    def __init__(self) -> None:
        self.slots = {}  # type: ignore
        self.batch_to_submit = {}  # type: ignore
        self.ready: List[int] = []
        self.submitted_dict: Dict[str, int] = {}
        self.submitted: List[int] = []
        self.running: List[int] = []
        self.completed: List[int] = []
        self.remaining: List[int] = []
        self.start = 0

    def get_run_time(self) -> str:
        seconds = round(default_timer() - self.start)
        return str(datetime.timedelta(seconds=seconds))

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
                if v in self.ready:
                    dependent_jobs = wf.in_edges(v)
                    with suppress(Exception):
                        dependent_jobs = list(set(dependent_jobs) - set(self.batch_to_submit[key]))

                    flag = False
                    for dependent_job in dependent_jobs:
                        if dependent_job not in self.completed:
                            flag = True
                            break

                    if not flag:
                        log(f"job {v} is ready to submit")
                        if key not in self.batch_to_submit:
                            self.batch_to_submit[key] = []

                        self.batch_to_submit[key].append(v)

    def G_sorted(self, G):
        my_list = []
        for node in list(G.nodes):
            if node != "\\n":
                my_list.append(int(node))

        return sorted(my_list)

    def batch_submit(self):
        for batch_key in self.batch_to_submit:
            G_copy = wf.G.copy()
            yaml_cfg = Yaml(yaml_fn_wf)
            yaml_cfg["config"]["source_code"]["path"] = str(BASE)
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
                yaml_cfg["config"]["dt_in"] = 200
                yaml_cfg["config"]["data_transfer_out"] = 0
                for u, v, d in wf.G.edges(data=True):
                    if int(u) in slots[batch_key] and int(v) in slots[batch_key]:
                        pass
                    else:
                        if u not in list(G_copy.nodes) and v in list(G_copy.nodes):
                            yaml_cfg["config"]["dt_in"] += int(d["weight"])

                        if u in list(G_copy.nodes) and v not in list(G_copy.nodes):
                            yaml_cfg["config"]["data_transfer_out"] += int(d["weight"])

                # yaml_cfg["config"]["data_transfer_out"] = yaml["config"]["jobs"][f"job{node}"]["dt_out"]
            elif self.batch_to_submit[batch_key]:
                yaml_cfg["config"]["jobs"] = {}
                yaml_cfg["config"]["dt_in"] = 200
                yaml_cfg["config"]["data_transfer_out"] = 0
                #: should start from the first job
                for node in list(G_copy.nodes):
                    _yaml = yaml_cfg["config"]["jobs"][f"job{node}"]
                    _yaml["cores"] = 1
                    _yaml["run_time"] = yaml["config"]["jobs"][f"job{node}"]["run_time"]
                    # yaml_cfg["config"]["data_transfer_out"] += yaml["config"]["jobs"][f"job{node}"]["dt_out"]

                for u, v, d in wf.G.edges(data=True):
                    if int(u) in slots[batch_key] and int(v) in slots[batch_key]:
                        pass
                    else:
                        if u not in list(G_copy.nodes) and v in list(G_copy.nodes):
                            yaml_cfg["config"]["dt_in"] += int(d["weight"])

                        if u in list(G_copy.nodes) and v not in list(G_copy.nodes):
                            yaml_cfg["config"]["data_transfer_out"] += int(d["weight"])

                if yaml_cfg["config"]["data_transfer_out"] == 0:
                    yaml_cfg["config"]["data_transfer_out"] = 250

                # print(yaml_cfg["config"]["dt_in"])
                # print(yaml_cfg["config"]["data_transfer_out"])
                # print(list(G_copy.nodes))

            job = Job()
            job.set_config(yaml_fn_wf)
            submit_ipfs(job)
            key = f"{job.info['provider']}_{job.info['jobKey']}_{job.info['index']}_{job.info['blockNumber']}"
            for node in self.G_sorted(G_copy):
                if node != "\\n":
                    try:
                        self.submitted_dict[key].append(int(node))
                    except:
                        self.submitted_dict[key] = [int(node)]

            with open(BASE / "heft_submitted_dict.pkl", "wb") as f:
                pickle.dump(self.submitted_dict, f)

            for node in list(G_copy.nodes):
                self.ready.remove(int(node))
                self.submitted.append(int(node))


def check_jobs(ewe):
    log(f"READY     => {ewe.ready}")
    log(f"SUBMITTED => {ewe.submitted}")
    log(f"RUNNING   => {ewe.running}")
    log(f"COMPLETED => {ewe.completed}")
    log()
    log(f"slots: {slots}")
    log(f"==> workflow_run_time={ewe.get_run_time()} {n} {edges}")
    log("-----------------------------------")
    for key, value in ewe.submitted_dict.items():
        for idx, val in enumerate(sorted(value)):
            if val in ewe.ready or val in ewe.submitted or val in ewe.running:
                keys = key.split("_")
                log(f"{val} => ", end="")
                _job = Ebb.get_job_info(keys[0], keys[1], keys[2], idx, keys[3], is_print=True)
                state_val = state.inv_code[_job["stateCode"]]
                if state_val == "SUBMITTED":
                    pass
                elif state_val == "RUNNING":
                    if val in ewe.submitted:
                        log(f"==> state changed to RUNNING for job: {val}")
                        ewe.submitted.remove(val)
                        ewe.running.append(val)
                elif state_val == "COMPLETED":
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
                            ewe.batch_submit()
                            return

                        # TODO: recursive check to submit new jobs


def main():
    ewe = Ewe()
    fn = BASE / "workflow_job.dot"
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

    log(f"slots: {slots}")
    slot_count = 0
    for slot in slots:
        slot_count += len(slots[slot])

    log(f"slot_count={slot_count}")
    if slot_count != n:
        raise Exception(f"E: Something is wrong at HEFT, node count should be {n}")

    ewe.slots = slots
    for node in list(wf.G_sorted()):
        ewe.ready.append(int(node))

    ewe.set_batch_to_submit()
    log(ewe.batch_to_submit)

    ewe.start = default_timer()
    ewe.batch_submit()
    while True:
        if not ewe.ready:
            break

        check_jobs(ewe)
        time.sleep(15)

    log(jobson)

    # finalizing
    log(f"==> final_heft_workflow_run_time={ewe.get_run_time()} {n} {edges}")
    with open(BASE / "heft_submitted_dict.pkl", "wb") as f:
        pickle.dump(ewe.submitted_dict, f)

    # heft_log.tex


if __name__ == "__main__":
    try:
        log("NEW_TEST -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
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
