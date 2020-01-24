import networkx as nx
from random import randint

G = nx.DiGraph()

# add 5 nodes, labeled 0-4:
map(G.add_node, range(5))
# 1,2 depend on 0:
G.add_edge(0, 1)
G.add_edge(0, 2)
# 3 depends on 1,2
G.add_edge(1, 3)
G.add_edge(2, 3)
# 4 depends on 1
G.add_edge(1, 4)

# now draw the graph:
pos = {0: (0, 0), 1: (1, 1), 2: (-1, 1), 3: (0, 2), 4: (2, 2)}
nx.draw(G, pos, edge_color="r")
