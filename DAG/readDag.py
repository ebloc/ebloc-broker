import networkx as nx
import matplotlib.pyplot as plt
import random, sys

jobIDs= {}

def notDependentSubmitJob(i):
    print('sbatch ' + i + '.sh')
    return random.randint(1,101)

def dependentSubmitJob(i, predecessors):
    if len(predecessors) == 1:
        print('sbatch --dependency=afterok:' + str(jobIDs[predecessors[0]]) + ' ' + i + '.sh')
        return random.randint(1,101)
    else:
        jobID_str = ""
        for j in predecessors:
            jobID_str += str(jobIDs[j]) + ':'

        jobID_str = jobID_str[:-1]
        # print(jobID_str)       
        print('sbatch --dependency=afterany:' + jobID_str + ' ' + i + '.sh')
        return random.randint(1,101)
    
G = nx.drawing.nx_pydot.read_dot('job.dot')
print(list(G.nodes))

for i in list(G.nodes):
    # print(i)
    
    if len(set(G.predecessors(i))) == 0:
        jobID = notDependentSubmitJob(i)
        jobIDs[i] = jobID
        print(jobID)
    else:
        jobID = dependentSubmitJob(i, list(G.predecessors(i)))
        jobIDs[i] = jobID
        print(jobID)
        print(list(G.predecessors(i)))
        # sys.exit()       
    print('-----------')



# jid4=$(sbatch  --dependency=afterany:$jid2:$jid3 job4.sh    
