#!/usr/bin/env python3

import matplotlib.pyplot as plt
import networkx as nx
import os
import random
import shutil
import sys
from pathlib import Path

from broker._utils.tools import print_tb
from broker._utils.yaml import Yaml
from broker.errors import QuietExit
from broker.workflow.Workflow import Workflow


def replace_str(fn, sleep_dur):
    with open(fn, "r") as file:
        filedata = file.read()

    filedata = filedata.replace("999", str(sleep_dur))
    with open(fn, "w") as file:
        file.write(filedata)


def main():
    BASE = Path.home() / "test_eblocbroker" / "test_data" / "base" / "source_code_wf_random"
    yaml_fn = BASE / "jobs.yaml"
    yaml = Yaml(yaml_fn)
    yaml["config"] = {}
    base_fn = Path.home() / "ebloc-broker" / "broker" / "test_setup_w" / "base.sh"
    if len(sys.argv) == 3:
        n = job_num = int(sys.argv[1])
        edges = int(sys.argv[2])
    else:
        n = job_num = 6
        edges = 8

    for fn in BASE.glob("job*.sh"):
        fn.unlink()  # deletes the file

    try:
        os.remove(BASE / "workflow_job.dot")
    except:
        pass

    try:
        os.remove(BASE / "job.png")
    except:
        pass

    wf = Workflow()
    while True:
        #: to be sure nodes are generated with the exact given node number
        wf.G = wf.generate_random_dag(n, edges)
        if len(list(wf.G.nodes)) == n:
            break
        # else:
        #     print(f"==> Trying again n={len(list(wf.G.nodes))}")

    print(f"{n} {edges}")
    nx.nx_pydot.write_dot(wf.G, BASE / "workflow_job.dot")
    nx.draw_spring(wf.G, with_labels=True)
    plt.savefig(BASE / "job.png")
    base_size = 200
    base_dt_out_size = 250
    for i in range(1, job_num + 1):
        # sleep_dur = random.randint(15, 30)
        sleep_dur = random.randint(2, 5)  # 2 <= x <= 5
        shutil.copyfile(base_fn, BASE / f"job{i}.sh")
        replace_str(BASE / f"job{i}.sh", sleep_dur * 60)
        _job = yaml["config"]["jobs"][f"job{i}"]
        _job["run_time"] = sleep_dur
        _job["cores"] = 1
        _job["dt_in"] = base_size
        _job["dt_out"] = 0
        dt_out = 0
        for edge in wf.out_edges(i):
            dt_out += wf.get_weight(i, edge)

        if dt_out:
            _job["dt_out"] = dt_out
        else:
            _job["dt_out"] = base_dt_out_size

        dt_in = 200  # base
        for edge in wf.in_edges(i):
            dt_in += wf.get_weight(edge, i)

        _job["dt_in"] = dt_in
        # breakpoint()  # DEBUG
        # print(i)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except QuietExit as e:
        print(f"#> {e}")
    except Exception as e:
        print_tb(str(e))
