import sys
import networkx as nx
import matplotlib.pyplot as plt

g = nx.Graph()
G = nx.DiGraph()

G.add_edge('A', 'B', weight=10)
G.add_edge('A', 'C', weight=0)
# 3 depends on 1,2
G.add_edge('B', 'D', weight=0)
G.add_edge('C', 'D', weight=0)
# 4 depends on 1
G.add_edge('B', 'job4', weight=0)
# 5 depends on 3 and 4
G.add_edge('C', 'E', weight=0)
G.add_edge('D', 'E', weight=10)

nx.nx_pydot.write_dot(G, 'job.dot') # Saves DAG into job.dot file

nx.draw(G, with_labels = True)
plt.savefig('labels.png')
