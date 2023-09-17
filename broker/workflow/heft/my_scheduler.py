#!/usr/bin/env python3

from heft.core import schedule
from pathlib import Path

from broker._utils._log import log
from broker._utils.tools import print_tb
from broker._utils.yaml import Yaml
from broker.errors import QuietExit
from broker.workflow.Workflow import Workflow

wf = Workflow()
yaml_fn = Path.home() / "ebloc-broker" / "broker" / "workflow" / "heft" / "jobs.yaml"
yaml = Yaml(yaml_fn)


provider_id = {}
provider_id["a"] = "p1"
provider_id["b"] = "p2"
provider_id["c"] = "p3"


def computation_cost(job, agent):
    # if agent == "a":
    #     return 20
    # elif agent == "b":
    #     return 18
    # else:
    #     return 15
    return yaml["jobs"][f"job{job}"]["cost"][provider_id[agent]]


def communication_cost(ni, nj, A, B):
    if A == B:
        return 0
    else:
        return wf.get_weight(ni, nj)


def main():
    slots = {}
    # fn = "/home/alper/test_eblocbroker/test_data/base/source_code_wf_random/workflow_job.dot"
    # wf.read_dot(fn)
    wf.read_dot("job.dot")
    dag = wf.dot_to_tuple()
    orders, jobson = schedule(dag, "abc", computation_cost, communication_cost)
    for key, _ in provider_id.items():
        for order in orders[key]:
            if key not in slots:
                slots[key] = [int(order.job)]
            else:
                slots[key].append(int(order.job))

    submitted_jobs = []
    ##
    batch_to_submit = []
    for key, value in slots.items():
        for v in value:
            dependent_jobs = wf.in_edges(v)
            flag = False
            if dependent_jobs:
                for dependent_job in dependent_jobs:
                    if dependent_job not in slots[key]:
                        flag = True
                        break

            if not flag:
                batch_to_submit.append(v)

    for job in batch_to_submit:
        submitted_jobs.append(job)

    log(batch_to_submit)
    # breakpoint()  # DEBUG
    # for order in sorted(orders):
    #     # breakpoint()  # DEBUG
    #     print(order, orders[order])

    # dependent_jobs = wf.in_edges(9)
    log(slots)
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
