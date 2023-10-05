#!/usr/bin/env python3

import datetime
import networkx as nx
import pickle
import random
import sys
import time
from contextlib import suppress
from pathlib import Path
from timeit import default_timer
from typing import Dict, List

from broker import cfg
from broker._utils import _log
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
_log.ll.LOG_FILENAME = Path.home() / ".ebloc-broker" / "test.log"
wf_sub = Workflow()
slots = {}  # type: ignore
_slots = {}  # type: ignore
_slots["a"] = []
_slots["b"] = []
_slots["c"] = []
#
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

BASE = Path.home() / "test_eblocbroker" / "workflow" / f"{n}_{edges}"
yaml_fn = BASE / "jobs.yaml"
yaml = Yaml(yaml_fn)

Ebb: "Contract.Contract" = cfg.Ebb
# BASE = Path.home() / "test_eblocbroker" / "test_data" / "base" / "source_code_wf_random"


class Ewe:
    def __init__(self) -> None:
        self.jobs_started_run_time = {}  # type: ignore
        self.slots = {}  # type: ignore
        self.batch_to_submit = {}  # type: ignore
        self.ready: List[int] = []
        self.submitted_dict: Dict[str, int] = {}
        self.submitted_node_dict: Dict[int, str] = {}
        self.submitted: List[int] = []
        self.running: List[int] = []
        self.completed: List[int] = []
        self.refunded: List[int] = []
        self.remaining: List[int] = []
        self.failed: List[int] = []
        self.start = 0
        self.submitted_wf = {}  # type: ignore

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
                        self.jobs_started_run_time[key] = default_timer()
                elif state_val == "COMPLETED":
                    if key in self.submitted or key in self.running:
                        log(f"==> state changed to COMPLETED for job: {key}")
                        with suppress(Exception):
                            self.submitted.remove(key)

                        with suppress(Exception):
                            self.running.remove(key)

                        self.completed.append(key)
                elif state_val == "REFUNDED":
                    if key in self.submitted or key in self.running:
                        log(f"==> state changed to REFUNDED for job: {key}")
                        with suppress(Exception):
                            self.submitted.remove(key)

                        with suppress(Exception):
                            self.running.remove(key)

                        self.refunded.append(key)

        with open(BASE / "layer_submitted_dict.pkl", "wb") as f:
            pickle.dump(self.submitted_node_dict, f)


def fetch_calcualted_cost(yaml_fn):
    """Fetch calcualted cost."""
    yaml_original = Yaml(yaml_fn)
    for address in yaml_original["config"]["costs"]:
        cost = yaml_original["config"]["costs"][address]
        print(cost)


def check_completed_jobs(ewe, dependent_jobs):
    for job_id in dependent_jobs:
        if job_id not in ewe.completed and job_id not in ewe.refunded and job_id not in ewe.failed:
            return False

    return True


def G_sorted(G):
    my_list = []
    for node in list(G.nodes):
        if node != "\\n":
            my_list.append(int(node))

    return sorted(my_list)


def split(a, n):
    k, m = divmod(len(a), n)
    return (a[i * k + min(i, m) : (i + 1) * k + min(i + 1, m)] for i in range(n))


def submit_layering():
    ewe = Ewe()
    yaml_fn = Path.home() / "ebloc-broker" / "broker" / "ipfs" / "job_workflow.yaml"
    yaml_original = Yaml(yaml_fn)
    yaml_fn_jobs = BASE / "jobs.yaml"
    yaml_jobs = Yaml(yaml_fn_jobs)
    fn = BASE / "workflow_job.dot"
    wf.read_dot(fn)
    for node in list(wf.G_sorted()):
        ewe.ready.append(int(node))

    last_submitted_provider = "z"
    slot_count = 0
    for idx, item in enumerate(wf.topological_generations()):
        if "\\n" in item:
            item.remove("\\n")

        node_list = list(map(int, item))
        # log(f"w{idx} => {sorted(node_list)}")
        slot_count += len(node_list)

    log(f"slot_count={slot_count}")
    if slot_count != n:
        raise Exception(f"E: Something is wrong at LAYER, node count should be {n}")

    #: DECIDE WHERE TO SUBMIT FIRST
    for idx, item in enumerate(wf.topological_generations()):
        if "\\n" in item:
            item.remove("\\n")

        node_list = list(map(int, item))
        G_copy = wf.G.copy()
        with suppress(Exception):
            G_copy.remove_node("\\n")

        for node in list(wf.G.nodes):
            if node != "\\n" and int(node) not in node_list:
                G_copy.remove_node(node)

        log(f"w{idx} => {sorted(node_list)} ")
        for idx, partial_layer in enumerate(list(split(sorted(node_list), 3))):
            for node in sorted(partial_layer):
                if idx == 0:
                    _slots["a"].append(node)
                elif idx == 1:
                    _slots["b"].append(node)
                elif idx == 2:
                    _slots["c"].append(node)
                else:
                    breakpoint()  # DEBUG

            # print(sorted(partial_layer))

        # if len(G_copy.edges) == 0:
        #     print("no edges")
        # else:
        #     log("edges", "green")

    log(_slots)
    start_flag = False
    log()
    ewe.start = default_timer()
    breakpoint()  # DEBUG
    while True:
        if not ewe.ready:
            break

        for idx, item in enumerate(wf.topological_generations()):
            if "\\n" in item:
                item.remove("\\n")

            node_list = list(map(int, item))
            break_flag = True
            for node in sorted(node_list):
                if wf.in_edges(node):
                    break_flag = False

            #: obtain list of all dependent jobs from the previous layers
            dependent_jobs = []
            for node in sorted(node_list):
                dependent_jobs = list(set(dependent_jobs + wf.in_edges(node)))

            # ? inner loop to find un-dependent part of the layer
            flag_me = False
            for job_id in dependent_jobs:
                if job_id in ewe.submitted or job_id in ewe.running:
                    flag_me = True
                    key = ewe.submitted_node_dict[job_id]
                    keys = key.split("_")
                    log(f"{job_id} ", end="")
                    job_info = Ebb.get_job_info(keys[0], keys[1], keys[2], keys[4], keys[3], is_print=False)
                    state_val = state.inv_code[job_info["stateCode"]]
                    if state_val != "COMPLETED":
                        #: only for print purposes
                        Ebb.get_job_info(keys[0], keys[1], keys[2], keys[4], keys[3], is_print=True)

                    if state_val == "RUNNING":
                        if job_id in ewe.submitted:
                            log(f"==> state changed to RUNNING for job: {job_id}")
                            ewe.submitted.remove(job_id)
                            ewe.running.append(job_id)
                            ewe.jobs_started_run_time[job_id] = default_timer()
                    elif state_val == "COMPLETED":
                        if job_id in ewe.submitted or job_id in ewe.running:
                            log(f"==> state changed to COMPLETED for job: {job_id}")
                            with suppress(Exception):
                                ewe.submitted.remove(job_id)

                            with suppress(Exception):
                                ewe.running.remove(job_id)

                            ewe.completed.append(job_id)
                    elif state_val == "REFUNDED":
                        if job_id in ewe.submitted or job_id in ewe.running:
                            log(f"==> state changed to REFUNDED for job: {job_id}")
                            with suppress(Exception):
                                ewe.submitted.remove(job_id)

                            with suppress(Exception):
                                ewe.running.remove(job_id)

                            ewe.refunded.append(job_id)

                    if job_id in ewe.running:
                        run_time = round(default_timer() - ewe.jobs_started_run_time[job_id])
                        if run_time > (int(yaml["config"]["jobs"][f"job{job_id}"]["run_time"]) + 5) * 60:
                            with suppress(Exception):
                                ewe.running.remove(job_id)

                            ewe.failed.append(job_id)

                #: all jobs should be completed for the given level
                if check_completed_jobs(ewe, dependent_jobs):
                    break_flag = True

                if flag_me:
                    ewe.update_job_stats()

            if idx == len(wf.topological_generations()) - 1:
                log(f"READY     => {ewe.ready}")
                log(f"SUBMITTED => {ewe.submitted}")
                log(f"RUNNING   => {ewe.running}")
                log(f"COMPLETED => {ewe.completed}")
                if ewe.refunded:
                    log(f"REFUNDED => {ewe.refunded}")

                if ewe.failed:
                    log(f"FAILED => {ewe.failed}")

                log()
                log(f"==> workflow_run_time={ewe.get_run_time()} {n} {edges} (layer)")
                if start_flag:
                    time.sleep(20)
            else:
                log("----------------------------------------------------------------------", "yellow")

            if not start_flag:
                start_flag = True

            try:
                ewe.submitted_wf[idx]
            except:
                ewe.submitted_wf[idx] = False

            # ? check dependency one-one-by submit some jobs in the layer early

            if break_flag and not ewe.submitted_wf[idx]:
                G_copy = wf.G.copy()
                with suppress(Exception):
                    G_copy.remove_node("\\n")

                for node in list(wf.G.nodes):
                    if node != "\\n" and int(node) not in node_list:
                        G_copy.remove_node(node)

                if len(G_copy.edges) == 0:  # always enters here
                    for _idx, partial_layer in enumerate(list(split(node_list, 3))):
                        continue_flag = False
                        if _idx == 0:
                            provider_char = "a"
                        if _idx == 1:
                            provider_char = "b"
                        if _idx == 2:
                            provider_char = "c"

                        G_copy = wf.G.copy()
                        with suppress(Exception):
                            G_copy.remove_node("\\n")

                        for node in list(wf.G.nodes):
                            if node != "\\n" and int(node) not in partial_layer:
                                G_copy.remove_node(node)

                        nx.nx_pydot.write_dot(G_copy, BASE / "sub_workflow_job.dot")
                        if len(partial_layer) > 1:
                            yaml_original["config"]["jobs"] = {}
                            for i, _job in enumerate(sorted(partial_layer)):
                                my_job = yaml_jobs["config"]["jobs"][f"job{_job}"]
                                yaml_original["config"]["jobs"][f"job{i + 1}"]["cores"] = 1
                                yaml_original["config"]["jobs"][f"job{i + 1}"]["run_time"] = my_job["run_time"]
                                yaml_original["config"]["dt_in"] = 200
                                yaml_original["config"]["data_transfer_out"] = 0
                                for u, v, d in wf.G.edges(data=True):
                                    if int(u) in _slots[provider_char] and int(v) in _slots[provider_char]:
                                        pass
                                    else:
                                        if u not in list(G_copy.nodes) and v in list(G_copy.nodes):
                                            yaml_original["config"]["dt_in"] += int(d["weight"])

                                        if u in list(G_copy.nodes) and v not in list(G_copy.nodes):
                                            yaml_original["config"]["data_transfer_out"] += int(d["weight"])
                        elif len(partial_layer) == 1:
                            my_job = yaml_jobs["config"]["jobs"][f"job{partial_layer[0]}"]
                            yaml_original["config"]["dt_in"] = my_job["dt_in"]
                            yaml_original["config"]["data_transfer_out"] = my_job["dt_out"]
                            yaml_original["config"]["jobs"] = {}
                            yaml_original["config"]["jobs"]["job1"]["cores"] = 1
                            yaml_original["config"]["jobs"]["job1"]["run_time"] = my_job["run_time"]
                        else:  #: if its empty
                            continue_flag = True

                        if not continue_flag:
                            yaml_original["config"]["provider_address"] = provider_id[provider_char]
                            yaml_original["config"]["source_code"]["path"] = str(BASE)
                            log(
                                f"* w{_idx} => {sorted(partial_layer)} | provider to submit => [bold cyan]{provider_char}[/bold cyan] "
                                "[orange]----------------------------------------------------"
                            )
                            job = Job()
                            job.set_config(yaml_fn)
                            submit_ipfs(job)  # submits the job
                            #
                            key = f"{job.info['provider']}_{job.info['jobKey']}_{job.info['index']}_{job.info['blockNumber']}"
                            for node in G_sorted(G_copy):
                                if node != "\\n":
                                    try:
                                        ewe.submitted_dict[key].append(int(node))
                                    except:
                                        ewe.submitted_dict[key] = [int(node)]

                            #: apply reverse map
                            for _idx, node in enumerate(sorted(partial_layer)):
                                ewe.submitted_node_dict[node] = f"{key}_{_idx}"

                            for node in list(G_copy.nodes):
                                ewe.ready.remove(int(node))
                                ewe.submitted.append(int(node))

                    ewe.submitted_wf[idx] = True
                else:
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
                    while True:
                        if provider_char == last_submitted_provider:
                            provider_char = random.choice("abc")
                        else:
                            break

                    last_submitted_provider = provider_char
                    yaml_original["config"]["provider_address"] = provider_id[provider_char]
                    yaml_original["config"]["source_code"]["path"] = str(BASE)
                    log(
                        f"* w{idx} => {sorted(node_list)} | provider to submit => [bold cyan]{provider_char}[/bold cyan] "
                        "[orange]----------------------------------------------------"
                    )
                    job = Job()
                    job.set_config(yaml_fn)
                    submit_ipfs(job)  # submits the job
                    ewe.submitted_wf[idx] = True
                    key = f"{job.info['provider']}_{job.info['jobKey']}_{job.info['index']}_{job.info['blockNumber']}"
                    for node in G_sorted(G_copy):
                        if node != "\\n":
                            try:
                                ewe.submitted_dict[key].append(int(node))
                            except:
                                ewe.submitted_dict[key] = [int(node)]

                    #: apply reverse map
                    for _idx, node in enumerate(sorted(node_list)):
                        ewe.submitted_node_dict[node] = f"{key}_{_idx}"

                    for node in list(G_copy.nodes):
                        ewe.ready.remove(int(node))
                        ewe.submitted.append(int(node))

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
        if ewe.refunded:
            log(f"REFUNDED => {ewe.refunded}")

        if ewe.failed:
            log(f"FAILED => {ewe.failed}")

        log()
        log(f"==> workflow_run_time=={ewe.get_run_time()} {n} {edges} (layer)")
        log("----------------------------------------------------------------------", "yellow")

    log(f"==> final_LAYER_by_layer_workflow_run_time={ewe.get_run_time()} {n} {edges}")


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
