#!/usr/bin/env python3


import matplotlib.pyplot as plt
import networkx as nx
import sys

g = nx.Graph()
G = nx.DiGraph()

"""
# add 5 nodes, labeled 0-4:
# map(G.add_node, range(5))
# 1,2 depend on 0:
G.add_edge('job0', 'job1', weight=10)
G.add_edge('job0', 'job2', weight=10)
# 3 depends on 1,2
G.add_edge('job1', 'job3', weight=10)
G.add_edge('job2', 'job3', weight=10)
# 4 depends on 1
G.add_edge('job1', 'job4', weight=10)
# 5 depends on 3 and 4
G.add_edge('job3', 'job5', weight=10)
G.add_edge('job4', 'job5', weight=10)
"""

G.add_edge("job0", "job5", weight=10)
G.add_edge("job1", "job5", weight=10)
G.add_edge("job2", "job5", weight=10)
G.add_edge("job3", "job5", weight=10)
G.add_edge("job4", "job5", weight=10)
G.add_edge("job6", "job0", weight=10)
G.add_edge("job7", "job0", weight=10)
G.add_edge("job8", "job7", weight=10)
G.add_edge("job9", "job7", weight=10)

# saves DAG into job.dot file
nx.nx_pydot.write_dot(G, "job.dot")

listG = list(G.nodes)

for i in list(G.nodes):
    print(i)
    print(set(G.predecessors(i)))

nx.draw(G, with_labels=True)
plt.savefig("labels.png")

sys.exit(0)

print(set(G.predecessors("job5")))


print([a[0] for a in G.edges() if a[1] == "job5"])
print([a[1] for a in G.edges() if a[0] == "job0"])
print([a[0] for a in G.edges() if a[1] == "job1"])
print(G.edges())

print(nx.ancestors(G, "job5"))
print(nx.descendants(G, "job0"))


"""
g.add_edges_from([('job1', 'job3')], weight=3)
g.add_edges_from([('job2', 'job3')], weight=3)
g.add_edges_from([('job3', 'job4')], weight=3)
g.add_edges_from([('job1', 'job5')], weight=3)

print(nx.descendants(g, 'job3'))
print(nx.ancestors(g, 'job3'))
"""

"""
g.add_edges_from([(1,2), (2,3), (2,4), (3,4)])
print(nx.descendants(g, 3))
print(nx.ancestors(g, 3))
"""

"""
g.add_edge('job2', 'job3', weight=4)
g.add_edge('job3', 'job4', weight=2)
g.add_edge('job1', 'job5', weight=3)
"""


# list(G.neighbors('job3'))
# print(G.edges('job3'))
# print(G.adjacency())


# print(list(G.adj['job3']))


"""
d = dict(g.degree)
print(d)
nx.draw(g, nodelist=d.keys(), node_size=[v * 100 for v in d.values()])
plt.show()
"""

"""
import networkx as nx
import matplotlib.pyplot as plt
G = nx.DiGraph()

# G is:
#      e-->f
#      ^
#      |
# a--->b-->c-->d
#

G.add_edges_from([('a', 'b'),('b', 'c'),('c', 'd'), ('b', 'e'), ('e', 'f')])
T = nx.dfs_tree(G.reverse(), source='f').reverse()

# T is: a-->b-->e-->f

pos = nx.nx_pydot.pydot_layout(T, prog='dot')
nx.draw_networkx(T, pos=pos, arrows= True, with_labels=True)
plt.show()
"""
