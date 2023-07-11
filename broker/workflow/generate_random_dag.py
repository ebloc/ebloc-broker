#!/usr/bin/env python3

import matplotlib.pyplot as plt
import networkx as nx
import random
from broker._utils._log import log
from broker._utils.tools import print_tb
from broker.errors import QuietExit
from broker.workflow.Workflow import Workflow
import networkx as nx


def _bfs_layers(G, node, map_scanned):
    for level in nx.bfs_layers(G, node):
        print(level)
        for item in level:
            map_scanned[item] = True


def main():
    n = 10
    w = Workflow()
    G = w.generate_random_dag(n, 15)
    w.G = G
    log(w.topological_sort())
    log(w.topological_generations())

    # log(w.bfs_layers([0, n - 1]))

    # map_scanned = {}
    # while True:
    #     # https://stackoverflow.com/a/75042802/2402577
    #     _bfs_layers(w.G, 0, map_scanned)
    #     if len(map_scanned) == n:
    #         break
    #     else:
    #         for item in range(n):
    #             if item not in map_scanned:
    #                 print("zzzzzzzzzzzzzzzzzzzzz")
    #                 _bfs_layers(w.G, [0, item], map_scanned)

    nx.draw(G, with_labels=True)
    plt.savefig("job.png")
    # nx.nx_pydot.write_dot(G, "job.dot")
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
