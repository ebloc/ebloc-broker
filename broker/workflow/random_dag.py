#!/usr/bin/env python3

import matplotlib.pyplot as plt
import networkx as nx
import random
from broker._utils._log import log
from broker._utils.tools import print_tb
from broker.errors import QuietExit


def main():
    # https://stackoverflow.com/a/13546785/2402577

    G = nx.gnp_random_graph(5, 0.5, directed=True)
    DAG = nx.DiGraph([(u, v, {"weight": random.randint(-10, 10)}) for (u, v) in G.edges() if u < v])
    breakpoint()  # DEBUG
    output = nx.is_directed_acyclic_graph(DAG)
    print(output)

    nx.draw(G, with_labels=True)

    plt.savefig("job.png")
    nx.nx_pydot.write_dot(G, "job.dot")
    # for i in list(G.nodes):
    #     print(i)
    #     print(set(G.predecessors(i)))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except QuietExit as e:
        print(f"#> {e}")
    except Exception as e:
        print_tb(str(e))
