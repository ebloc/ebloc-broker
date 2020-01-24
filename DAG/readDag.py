#!/usr/bin/env python3

import networkx as nx
import matplotlib.pyplot as plt
import random, sys

jobIDs = {}


def dependencyJob(i):
    if len(set(G.predecessors(i))) == 0:
        jobID = notDependentSubmitJob(i)
        jobIDs[i] = jobID
        print("jobID: " + str(jobID))
    else:
        jobID = dependentSubmitJob(i, list(G.predecessors(i)))
        jobIDs[i] = jobID
        print("jobID: " + str(jobID))
        print(list(G.predecessors(i)))
        # sys.exit()


def notDependentSubmitJob(i):
    print("sbatch " + i + ".sh")
    return random.randint(1, 101)


def dependentSubmitJob(i, predecessors):
    if len(predecessors) == 1:
        if not predecessors[0] in jobIDs:  # If the required job is not submitted to Slurm, recursive call
            dependencyJob(predecessors[0])

        print("sbatch --dependency=afterok:" + str(jobIDs[predecessors[0]]) + " " + i + ".sh")
        return random.randint(1, 101)
    else:
        jobID_str = ""

        for j in predecessors:
            if not j in jobIDs:  # If the required job is not submitted to Slurm, recursive call
                dependencyJob(j)

            jobID_str += str(jobIDs[j]) + ":"

        jobID_str = jobID_str[:-1]
        # print(jobID_str)
        print("sbatch --dependency=afterok:" + jobID_str + " " + i + ".sh")
        return random.randint(1, 101)


G = nx.drawing.nx_pydot.read_dot("job.dot")

print("List of nodes:")
print(list(G.nodes))

for i in list(G.nodes):
    # print(i)
    # print(len(set(G.successors(i))))
    if not i in jobIDs:
        dependencyJob(i)


for i in list(G.nodes):
    print(i + " " + str(jobIDs[i]))

# jid4=$(sbatch  --dependency=afterany:$jid2:$jid3 job4.sh
