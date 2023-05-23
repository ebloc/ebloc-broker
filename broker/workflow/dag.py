#!/usr/bin/env python3

import sys
import networkx as nx
import matplotlib.pyplot as plt
from broker._utils._log import log


def basic():
    # Create an empty graph
    G = nx.Graph()

    # Add nodes to the graph
    G.add_node(1)
    G.add_node(2)
    G.add_node(3)

    # Add edges to the graph
    G.add_edge(1, 2)
    G.add_edge(2, 3)
    G.add_edge(3, 1)

    # Draw the graph
    nx.draw(G, with_labels=True)
    plt.show()


def main():
    G = nx.DiGraph()
    G.add_edges_from([("A", "D"), ("B", "D"), ("C", "D"), ("A", "E"), ("B", "E"), ("C", "E"), ("D", "F"), ("E", "F")])
    # # explicitly set positions
    # pos = {1: (0, -1), 2: (0, 0), 3: (1, 0), 4: (4, 0.255), 5: (5, 0.03), 5: (6, 0.03)}

    nx.draw_networkx(G)
    ax = plt.gca()
    ax.margins(0.20)
    plt.axis("off")
    # plt.show()

    print(G.nodes())
    log(nx.to_dict_of_dicts(G))
    breakpoint()  # DEBUG
    print(list(nx.topological_sort(G)))


if __name__ == "__main__":
    try:
        # basic()
        main()
    except KeyboardInterrupt:
        sys.exit(1)

# nx.shortest_path(G, "A", "D", weight="weight")


# #!/usr/bin/env python3

# import networkx as nx


# triangle_graph = nx.from_edgelist([(1, 2), (2, 3), (3, 1)], create_using=nx.DiGraph)
# nx.draw_planar(
#     triangle_graph,
#     with_labels=True,
#     node_size=1000,
#     node_color="#ffff8f",
#     width=0.8,
#     font_size=14,
# )

# G = nx.Graph()
# G.add_edge(1, 2)
# G.add_edge(1, 3)
# G.add_edge(1, 5)
# G.add_edge(2, 3)
# G.add_edge(3, 4)
# G.add_edge(4, 5)


# options = {
#     "font_size": 36,
#     "node_size": 3000,
#     "node_color": "white",
#     "edgecolors": "black",
#     "linewidths": 5,
#     "width": 5,
# }


# Set margins for the axes so that nodes aren't clipped


# import networkx as nx

# G = nx.DiGraph()

# # add 5 nodes, labeled 0-4:
# map(G.add_node, range(5))
# # 1,2 depend on 0:
# G.add_edge(0, 1)
# G.add_edge(0, 2)
# # 3 depends on 1,2
# G.add_edge(1, 3)
# G.add_edge(2, 3)
# # 4 depends on 1
# G.add_edge(1, 4)

# # now draw the graph:
# pos = {0: (0, 0), 1: (1, 1), 2: (-1, 1), 3: (0, 2), 4: (2, 2)}
# nx.draw(G, pos, edge_color="r")
# print("end")
