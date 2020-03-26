#!/usr/bin/env python3

import random

import networkx as nx

job_ids = {}


def dependencyJob(i):
    if not len(set(G.predecessors(i))):
        job_id = notDependentSubmitJob(i)
        job_ids[i] = job_id
        print("job_id: " + str(job_id))
    else:
        job_id = dependentSubmitJob(i, list(G.predecessors(i)))
        job_ids[i] = job_id
        print("job_id: " + str(job_id))
        print(list(G.predecessors(i)))
        # sys.exit()


def notDependentSubmitJob(i):
    print("sbatch " + i + ".sh")
    return random.randint(1, 101)


def dependentSubmitJob(i, predecessors):
    if len(predecessors) == 1:
        if not predecessors[0] in job_ids:  # If the required job is not submitted to Slurm, recursive call
            dependencyJob(predecessors[0])

        print("sbatch --dependency=afterok:" + str(job_ids[predecessors[0]]) + " " + i + ".sh")
        return random.randint(1, 101)
    else:
        job_id_str = ""

        for j in predecessors:
            if j not in job_ids:  # If the required job is not submitted to Slurm, recursive call
                dependencyJob(j)

            job_id_str += str(job_ids[j]) + ":"

        job_id_str = job_id_str[:-1]
        # print(job_id_str)
        print("sbatch --dependency=afterok:" + job_id_str + " " + i + ".sh")
        return random.randint(1, 101)


G = nx.drawing.nx_pydot.read_dot("job.dot")

print("List of nodes:")
print(list(G.nodes))

for i in list(G.nodes):
    # print(i)
    # print(len(set(G.successors(i))))
    if i not in job_ids:
        dependencyJob(i)


for i in list(G.nodes):
    print(i + " " + str(job_ids[i]))

# jid4=$(sbatch  --dependency=afterany:$jid2:$jid3 job4.sh
