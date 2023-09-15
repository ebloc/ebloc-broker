#!/usr/bin/env python3

from broker.lib import state
import time
from typing import List, Dict
from broker.ipfs.submit import submit_ipfs
import random
import networkx as nx
from contextlib import suppress
from broker._utils._log import log
from broker._utils.tools import print_tb
from broker.errors import QuietExit
from broker.workflow.Workflow import Workflow
from broker import cfg
from broker.eblocbroker_scripts import Contract
from pathlib import Path
from broker._utils.yaml import Yaml
from broker.eblocbroker_scripts.job import Job
from broker.ipfs.submit_w import submit_ipfs_calc

wf = Workflow()
provider_id = {}
provider_id["a"] = "0x29e613B04125c16db3f3613563bFdd0BA24Cb629"
provider_id["b"] = "0x4934a70Ba8c1C3aCFA72E809118BDd9048563A24"
provider_id["c"] = "0xe2e146d6B456760150d78819af7d276a1223A6d4"

Ebb: "Contract.Contract" = cfg.Ebb


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


def job_progress(ewe, job_id):
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


def submit_layering():
    ewe = Ewe()
    yaml_fn = Path.home() / "ebloc-broker" / "broker" / "ipfs" / "job_workflow.yaml"
    yaml_original = Yaml(yaml_fn)
    BASE = Path.home() / "test_eblocbroker" / "test_data" / "base" / "source_code_wf_random"
    yaml_fn_jobs = BASE / "jobs.yaml"
    yaml_jobs = Yaml(yaml_fn_jobs)

    fn = "/home/alper/test_eblocbroker/test_data/base/source_code_wf_random/workflow_job.dot"
    wf.read_dot(fn)
    for node in list(wf.G_sorted()):
        ewe.ready.append(int(node))

    for idx, item in enumerate(wf.topological_generations()):
        if "\\n" in item:
            item.remove("\\n")

        node_list = list(map(int, item))
        log(f"w{idx} => {sorted(node_list)}")

    log()
    for idx, item in enumerate(wf.topological_generations()):
        if "\\n" in item:
            item.remove("\\n")

        node_list = list(map(int, item))
        log(f"* w{idx} => {sorted(node_list)}")

        # wait till there is no dependency
        while True:
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

            time.sleep(5)
            log(f"READY     => {ewe.ready}")
            log(f"SUBMITTED => {ewe.submitted}")
            log(f"RUNNING   => {ewe.running}")
            log(f"COMPLETED => {ewe.completed}")
            log("-----------------------------------")

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
        provider_char = "a"  # DELETEME
        yaml_original["config"]["provider_address"] = provider_id[provider_char]
        log(f"==> provider to submit => [bold cyan]{provider_char}[/bold cyan]")
        job = Job()
        job.set_config(yaml_fn)
        submit_ipfs(job)  # submits the job
        key = f"{job.info['provider']}_{job.info['jobKey']}_{job.info['index']}_{job.info['blockNumber']}"
        for node in list(G_copy.nodes):
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

        # submit_ipfs_calc(job, is_verbose=False)
        ####

        # fetch_calcualted_cost(yaml_fn)

    #: Check for the final submitted layer
    while True:
        if not ewe.submitted and not ewe.running:
            break

        for job_id in ewe.submitted:
            job_progress(ewe, job_id)

        for job_id in ewe.running:
            job_progress(ewe, job_id)

        time.sleep(5)
        log(f"READY     => {ewe.ready}")
        log(f"SUBMITTED => {ewe.submitted}")
        log(f"RUNNING   => {ewe.running}")
        log(f"COMPLETED => {ewe.completed}")
        log("-----------------------------------")

    breakpoint()  # DEBUG


def main():
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
