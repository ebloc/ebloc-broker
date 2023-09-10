#!/usr/bin/env python3

from contextlib import suppress
import networkx as nx
from broker._utils.yaml import Yaml
from pathlib import Path
from broker._utils.tools import print_tb
from broker.errors import QuietExit
from heft.core import schedule
from broker.workflow.Workflow import Workflow
from broker._utils._log import log

wf = Workflow()
yaml_fn = Path.home() / "test_eblocbroker" / "test_data/base" / "source_code_wf_random" / "jobs.yaml"
yaml = Yaml(yaml_fn)

provider_id = {}
provider_id["a"] = "0x29e613B04125c16db3f3613563bFdd0BA24Cb629"
provider_id["b"] = "0x4934a70Ba8c1C3aCFA72E809118BDd9048563A24"
provider_id["c"] = "0xe2e146d6B456760150d78819af7d276a1223A6d4"


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


def main():
    BASE = Path.home() / "test_eblocbroker" / "test_data" / "base" / "source_code_wf_random"
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
    ewe.set_batch_to_submit()
    log(ewe.batch_to_submit)

    for batch_key in ewe.batch_to_submit:
        G_copy = wf.G.copy()
        if ewe.batch_to_submit[batch_key]:
            g_list = []
            for node in list(wf.G.nodes):
                if node != "\\n" and int(node) not in ewe.batch_to_submit[batch_key]:
                    g_list.append(node)

            with suppress(Exception):
                G_copy.remove_node("\\n")

            for key in g_list:
                G_copy.remove_node(key)

            nx.nx_pydot.write_dot(G_copy, BASE / "sub_workflow_job.dot")
            breakpoint()  # DEBUG
            # submit job

    ##########################################################################################
    submitted_jobs = []
    while True:
        running = []
        completed = []
        ready = []
        remaining = []
        """
        for iterate jobs:
            # fill lists into temp

        if is any list changes
            ... # recursive check to submit new jobs
        else:
            # lists = temp_list

        # sleep(15)
        """

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
