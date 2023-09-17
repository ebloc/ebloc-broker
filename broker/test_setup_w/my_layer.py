#!/usr/bin/env python3

import sys
import datetime
import networkx as nx
import pickle
import random
import time
from contextlib import suppress
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
provider_id = {}
provider_id["a"] = "0x29e613B04125c16db3f3613563bFdd0BA24Cb629"
provider_id["b"] = "0x4934a70Ba8c1C3aCFA72E809118BDd9048563A24"
provider_id["c"] = "0xe2e146d6B456760150d78819af7d276a1223A6d4"

if len(sys.argv) == 3:
    n = int(sys.argv[1])
    edges = int(sys.argv[2])
else:
    n = 10
    edges = 10

BASE_SAVE = Path.home() / "test_eblocbroker" / "workflow" / f"{n}_{edges}"

Ebb: "Contract.Contract" = cfg.Ebb
BASE = Path.home() / "test_eblocbroker" / "test_data" / "base" / "source_code_wf_random"


class Ewe:
    def __init__(self) -> None:
        self.slots = {}  # type: ignore
        self.batch_to_submit = {}  # type: ignore
        self.ready: List[int] = []
        self.submitted_dict: Dict[str, int] = {}
        self.submitted_node_dict: Dict[int, str] = {}
        self.submitted: List[int] = []
        self.running: List[int] = []
        self.completed: List[int] = []
        self.remaining: List[int] = []
        self.start = 0

    def get_run_time(self) -> str:
        seconds = round(default_timer() - self.start)
        return str(datetime.timedelta(seconds=seconds))

    def update_job_stats(self):
        for key, value in self.submitted_node_dict.items():
            key = int(key)
            if key in self.ready or key in self.submitted or key in self.running:
                keys = value.split("_")
                job_info = Ebb.get_job_info(keys[0], keys[1], keys[2], keys[4], keys[3], is_print=False)
                state_val = state.inv_code[job_info["stateCode"]]
                if state_val == "RUNNING":
                    if key in self.submitted:
                        log(f"==> state changed to RUNNING for job: {key}")
                        self.submitted.remove(key)
                        self.running.append(key)
                elif state_val == "COMPLETED":
                    if key in self.submitted or key in self.running:
                        log(f"==> state changed to COMPLETED for job: {key}")
                        with suppress(Exception):
                            self.submitted.remove(key)

                        with suppress(Exception):
                            self.running.remove(key)

                        self.completed.append(key)

        with open(BASE_SAVE / "layer_submitted_dict.pkl", "wb") as f:
            pickle.dump(self.submitted_node_dict, f)


def fetch_calcualted_cost(yaml_fn):
    """Fetch calcualted cost."""
    yaml_original = Yaml(yaml_fn)
    for address in yaml_original["config"]["costs"]:
        cost = yaml_original["config"]["costs"][address]
        print(cost)


def check_completed_jobs(ewe, dependent_jobs):
    for job_id in dependent_jobs:
        if job_id not in ewe.completed:
            return False

    return True


def G_sorted(G):
    my_list = []
    for node in list(G.nodes):
        if node != "\\n":
            my_list.append(int(node))

    return sorted(my_list)


def submit_layering():
    ewe = Ewe()
    yaml_fn = Path.home() / "ebloc-broker" / "broker" / "ipfs" / "job_workflow.yaml"
    yaml_original = Yaml(yaml_fn)
    yaml_fn_jobs = BASE / "jobs.yaml"
    yaml_jobs = Yaml(yaml_fn_jobs)

    fn = "/home/alper/test_eblocbroker/test_data/base/source_code_wf_random/workflow_job.dot"
    wf.read_dot(fn)
    for node in list(wf.G_sorted()):
        ewe.ready.append(int(node))

    slot_count = 0
    for idx, item in enumerate(wf.topological_generations()):
        if "\\n" in item:
            item.remove("\\n")

        node_list = list(map(int, item))
        log(f"w{idx} => {sorted(node_list)}")
        slot_count += len(node_list)

    log(f"slot_count={slot_count}")
    if slot_count != n:
        raise Exception(f"E: Something is wrong at HEFT, node count should be {n}")

    log()
    ewe.start = default_timer()
    for idx, item in enumerate(wf.topological_generations()):
        if "\\n" in item:
            item.remove("\\n")

        node_list = list(map(int, item))
        while True:  #: wait till there is no dependency
            break_flag = True
            for node in sorted(node_list):
                if wf.in_edges(node):
                    break_flag = False

            #: obtain list of all dependent jobs from the previous layers
            dependent_jobs = []
            for node in sorted(node_list):
                dependent_jobs = list(set(dependent_jobs + wf.in_edges(node)))

            for job_id in dependent_jobs:
                key = ewe.submitted_node_dict[job_id]
                keys = key.split("_")
                job_info = Ebb.get_job_info(keys[0], keys[1], keys[2], keys[4], keys[3], is_print=True)
                state_val = state.inv_code[job_info["stateCode"]]
                if state_val == "RUNNING":
                    if job_id in ewe.submitted:
                        log(f"==> state changed to RUNNING for job: {job_id}")
                        ewe.submitted.remove(job_id)
                        ewe.running.append(job_id)
                elif state_val == "COMPLETED":
                    if job_id in ewe.submitted or job_id in ewe.running:
                        log(f"==> state changed to COMPLETED for job: {job_id}")
                        with suppress(Exception):
                            ewe.submitted.remove(job_id)

                        with suppress(Exception):
                            ewe.running.remove(job_id)

                        ewe.completed.append(job_id)

                #: all jobs should be completed
                output = check_completed_jobs(ewe, dependent_jobs)
                if output:
                    break_flag = True

            if break_flag:
                break

            time.sleep(20)
            log(f"READY     => {ewe.ready}")
            log(f"SUBMITTED => {ewe.submitted}")
            log(f"RUNNING   => {ewe.running}")
            log(f"COMPLETED => {ewe.completed}")
            log()
            log(f"==> workflow_run_time={ewe.get_run_time()}")
            log("-----------------------------------")
            ewe.update_job_stats()

        G_copy = wf.G.copy()
        with suppress(Exception):
            G_copy.remove_node("\\n")

        for node in list(wf.G.nodes):
            if node != "\\n" and int(node) not in node_list:
                G_copy.remove_node(node)

        nx.nx_pydot.write_dot(G_copy, BASE / "sub_workflow_job.dot")
        if len(node_list) > 1:
            yaml_original["config"]["jobs"] = {}
            for i, _job in enumerate(sorted(node_list)):
                my_job = yaml_jobs["config"]["jobs"][f"job{_job}"]
                yaml_original["config"]["jobs"][f"job{i + 1}"]["cores"] = 1
                yaml_original["config"]["jobs"][f"job{i + 1}"]["run_time"] = my_job["run_time"]
                yaml_original["config"]["dt_in"] = 200
                yaml_original["config"]["data_transfer_out"] = 0
                for u, v, d in wf.G.edges(data=True):
                    if int(u) in item and int(v) in item:
                        pass
                    else:
                        if u not in list(G_copy.nodes) and v in list(G_copy.nodes):
                            yaml_original["config"]["dt_in"] += int(d["weight"])

                        if u in list(G_copy.nodes) and v not in list(G_copy.nodes):
                            yaml_original["config"]["data_transfer_out"] += int(d["weight"])
        else:
            my_job = yaml_jobs["config"]["jobs"][f"job{node_list[0]}"]
            yaml_original["config"]["dt_in"] = my_job["dt_in"]
            yaml_original["config"]["data_transfer_out"] = my_job["dt_out"]
            yaml_original["config"]["jobs"] = {}
            yaml_original["config"]["jobs"]["job1"]["cores"] = 1
            yaml_original["config"]["jobs"]["job1"]["run_time"] = my_job["run_time"]

        provider_char = random.choice("abc")
        yaml_original["config"]["provider_address"] = provider_id[provider_char]
        log(
            f"* w{idx} => {sorted(node_list)} | provider to submit => [bold cyan]{provider_char}[/bold cyan] "
            "[orange]-----------------------------------------------"
        )
        job = Job()
        job.set_config(yaml_fn)
        submit_ipfs(job)  # submits the job
        key = f"{job.info['provider']}_{job.info['jobKey']}_{job.info['index']}_{job.info['blockNumber']}"
        for node in G_sorted(G_copy):
            if node != "\\n":
                try:
                    ewe.submitted_dict[key].append(int(node))
                except:
                    ewe.submitted_dict[key] = [int(node)]

        #: apply reverse map
        for idx, node in enumerate(sorted(node_list)):
            ewe.submitted_node_dict[node] = f"{key}_{idx}"

        for node in list(G_copy.nodes):
            ewe.ready.remove(int(node))
            ewe.submitted.append(int(node))

        ####

        # fetch_calcualted_cost(yaml_fn)

    #: Check for the final submitted layer
    while True:
        if not ewe.submitted and not ewe.running:
            break

        ewe.update_job_stats()
        time.sleep(5)
        log(f"READY     => {ewe.ready}")
        log(f"SUBMITTED => {ewe.submitted}")
        log(f"RUNNING   => {ewe.running}")
        log(f"COMPLETED => {ewe.completed}")
        log()
        log(f"==> final_workflow_run_time={ewe.get_run_time()}")
        log("-----------------------------------")


def main():
    log("NEW_TEST -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
    submit_layering()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except QuietExit as e:
        print(f"#> {e}")
    except Exception as e:
        print_tb(str(e))
