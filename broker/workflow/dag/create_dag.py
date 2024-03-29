#!/usr/bin/env python3

import matplotlib.pyplot as plt
import networkx as nx
import sys

from broker._utils.tools import print_tb
from broker.errors import QuietExit


def main():
    G = nx.DiGraph()

    # jobs
    # G.add_edge(0, 5, weight=10)
    G.add_edge(0, 5)
    G.add_edge(1, 5)
    G.add_edge(2, 5)
    G.add_edge(3, 5)
    G.add_edge(4, 5)
    G.add_edge(6, 0)
    G.add_edge(7, 0)
    G.add_edge(8, 7)
    G.add_edge(9, 7)

    # saves DAG into job.dot file
    nx.nx_pydot.write_dot(G, "job.dot")
    for i in list(G.nodes):
        print(i)
        print(set(G.predecessors(i)))

    nx.draw(G, with_labels=True)
    plt.savefig("job.png")

    sys.exit(1)

    print(set(G.predecessors(5)))
    print([a[0] for a in G.edges() if a[1] == 5])
    print([a[1] for a in G.edges() if a[0] == 0])
    print([a[0] for a in G.edges() if a[1] == 1])
    print(G.edges())
    print(nx.ancestors(G, 5))
    print(nx.descendants(G, 0))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except QuietExit as e:
        print(f"==> {e}")
    except Exception as e:
        print_tb(str(e))

"""
# add 5 nodes, labeled 0-4:
# map(G.add_node, range(5))
# 1,2 depend on 0:
G.add_edge('job0', 'job1')
G.add_edge('job0', 'job2')
# 3 depends on 1,2
G.add_edge('job1', 'job3')
G.add_edge('job2', 'job3')
# 4 depends on 1
G.add_edge('job1', 'job4')
# 5 depends on 3 and 4
G.add_edge('job3', 'job5')
G.add_edge('job4', 'job5')
"""

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
