#!/usr/bin/env python3

import datetime
import networkx as nx
import pickle
import sys
import time
from contextlib import suppress
from heft.core import schedule
from pathlib import Path
from timeit import default_timer
from typing import Dict, List

from broker import cfg
from broker._utils import _log
from broker._utils._log import log
from broker._utils.tools import get_online_idle_core, print_tb
from broker._utils.yaml import Yaml
from broker.eblocbroker_scripts import Contract
from broker.eblocbroker_scripts.job import Job
from broker.errors import QuietExit
from broker.ipfs.submit import submit_ipfs
from broker.lib import state
from broker.workflow.Workflow import Workflow

#: >10 running jobs should be carried to FAILED

wf = Workflow()

_log.ll.LOG_FILENAME = Path.home() / ".ebloc-broker" / "test.log"

is_load = False

if len(sys.argv) == 4:
    n = int(sys.argv[1])
    edges = int(sys.argv[2])
    load = str(sys.argv[3])
    if load == "load":
        is_load = True
elif len(sys.argv) == 3:
    n = int(sys.argv[1])
    edges = int(sys.argv[2])
else:
    print("Please provide node and edge number as argument")
    sys.exit(1)
    # n = 10
    # edges = 10

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

provider_ip = {}
provider_ip["a"] = "192.168.1.117"
provider_ip["b"] = "192.168.1.21"
provider_ip["c"] = "192.168.1.104"

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
        self.jobs_started_run_time = {}  # type: ignore
        self.slots = {}  # type: ignore
        self.batch_to_submit = {}  # type: ignore
        self.ready: List[int] = []
        self.submitted_dict: Dict[str, int] = {}
        self.submitted: List[int] = []
        self.running: List[int] = []
        self.completed: List[int] = []
        self.remaining: List[int] = []
        self.refunded: List[int] = []
        self.failed: List[int] = []
        self.start = 0
        self.very_first_job = {}
        self.very_first_job["a"] = True
        self.very_first_job["b"] = True
        self.very_first_job["c"] = True

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
                        if (
                            dependent_job in self.ready
                            or dependent_job in self.submitted
                            or dependent_job in self.running
                        ):
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
            #: Load -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
            if not is_load:
                yaml_cfg["config"]["provider_address"] = provider_id[batch_key]
            else:
                idle_code = get_online_idle_core(provider_ip[batch_key])
                log(f"provider {batch_key} idle cores: {idle_code}")
                if idle_code > 0:
                    yaml_cfg["config"]["provider_address"] = provider_id[batch_key]
                else:
                    yaml_cfg["config"]["provider_address"] = provider_id[batch_key]
                    for pr in provider_ip:
                        idle_code = get_online_idle_core(provider_ip[pr])
                        if idle_code > 0:
                            print(
                                f"#: Load changed to provider={pr} #########################################################################"
                            )
                            yaml_cfg["config"]["provider_address"] = provider_id[pr]
                            break
            # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
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
                if self.very_first_job[batch_key]:
                    yaml_cfg["config"]["dt_in"] = 201
                    self.very_first_job[batch_key] = False
                else:
                    yaml_cfg["config"]["dt_in"] = 0

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

                if self.very_first_job[batch_key]:
                    yaml_cfg["config"]["dt_in"] = 201
                    self.very_first_job[batch_key] = False
                else:
                    yaml_cfg["config"]["dt_in"] = 0

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
            print(f"dt_in={yaml_cfg['config']['dt_in']}")
            while True:
                try:
                    submit_ipfs(job)  # submits the job
                    break
                except:
                    pass

            key = f"{job.info['provider']}_{job.info['jobKey']}_{job.info['index']}_{job.info['blockNumber']}"
            for node in self.G_sorted(G_copy):
                if node != "\\n":
                    try:
                        self.submitted_dict[key].append(int(node))
                    except:
                        self.submitted_dict[key] = [int(node)]

            #: save operation is done
            with open(BASE / "heft_submitted_dict.pkl", "wb") as f:
                pickle.dump(self.submitted_dict, f)

            for node in list(G_copy.nodes):
                if node != "\\n":
                    try:
                        self.ready.remove(int(node))
                    except:
                        print(node)
                        log("================================================== something is wrong")

                    if int(node) not in self.submitted:
                        self.submitted.append(int(node))


def check_jobs(ewe):
    log(f"READY     => {ewe.ready}")
    log(f"SUBMITTED => {ewe.submitted}")
    log(f"RUNNING   => {ewe.running}")
    if ewe.completed:
        log(f"COMPLETED => {ewe.completed}")

    if ewe.refunded:
        log(f"REFUNDED => {ewe.refunded}")

    if ewe.failed:
        log(f"FAILED => {ewe.failed}")

    for job in ewe.jobs_started_run_time:
        if job in ewe.running:
            run_time = round(default_timer() - ewe.jobs_started_run_time[job])
            if run_time > (int(yaml["config"]["jobs"][f"job{job}"]["run_time"]) + 2) * 60:
                log(f"* CHECKME {job} <======================", "alert")

    """
    for job in ewe.jobs_started_run_time:
        if job in ewe.running:
            run_time = round(default_timer() - ewe.jobs_started_run_time[job])
            if run_time > (int(yaml["config"]["jobs"][f"job{job}"]["run_time"]) + 10) * 60:
                with suppress(Exception):
                    ewe.running.remove(job)

                ewe.failed.append(job)
    """

    log()
    # log("slots:")
    # log(f"a => {sorted(slots['a'])}")
    # log(f"b => {sorted(slots['b'])}")
    # log(f"c => {sorted(slots['c'])}")
    log(f"==> workflow_run_time={ewe.get_run_time()} {n} {edges} (heft)")
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
                        ewe.jobs_started_run_time[val] = default_timer()
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
                elif state_val == "REFUNDED":
                    if val in ewe.submitted or val in ewe.running:
                        log(f"==> state changed to REFUNDED for job: {val}")
                        with suppress(Exception):
                            ewe.submitted.remove(val)

                        with suppress(Exception):
                            ewe.running.remove(val)

                        ewe.refunded.append(val)
                        if ewe.batch_to_submit:
                            log(ewe.batch_to_submit)
                            ewe.batch_submit()
                            return

                if val in ewe.running:
                    run_time = round(default_timer() - ewe.jobs_started_run_time[val])
                    if run_time > (int(yaml["config"]["jobs"][f"job{val}"]["run_time"]) + 5) * 60:
                        with suppress(Exception):
                            ewe.running.remove(val)

                        ewe.failed.append(val)


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
        time.sleep(60)

    log("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-", "yellow")
    while True:
        #: with for on-going jobs to finish
        if not ewe.submitted and not ewe.running:
            break

        check_jobs(ewe)
        time.sleep(60)

    # log(jobson)
    # log("========================================================================")
    # while True:
    #     if not ewe.submitted and not ewe.running:
    #         break

    # finalizing
    total_run_time = ewe.get_run_time()
    log(f"==> final_HEFT_workflow_run_time={total_run_time} {n} {edges}")
    with open(BASE / "heft_submitted_dict.pkl", "wb") as f:
        pickle.dump(ewe.submitted_dict, f)


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
