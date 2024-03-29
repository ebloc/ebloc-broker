#!/usr/bin/env python3

import matplotlib.pyplot as plt
import networkx as nx

from broker._utils._log import log
from broker._utils.tools import print_tb
from broker.errors import QuietExit
from broker.workflow.Workflow import Workflow


def _bfs_layers(G, node, map_scanned):
    for level in nx.bfs_layers(G, node):
        print(level)
        for item in level:
            map_scanned[item] = True


def is_there_edges(G):
    for node, out_degree in G.out_degree():
        if out_degree == 0:
            pass
        else:
            return True

    return False


def main():
    n = 5
    edges = 5
    # n = 15
    # edges = 20
    ############
    wf = Workflow()
    G = wf.generate_random_dag(n, edges)
    wf.G = G
    log(wf.topological_sort())
    log(wf.topological_generations())
    for item in enumerate(nx.topological_generations(wf.G)):
        print(item)  # nodes in the layer can run in parallel
        _G = nx.DiGraph()
        for _item in item[1]:
            _G.add_node(_item)

        # nx.nx_pydot.write_dot(_G, f"G{item[0]}.dot")
        #
        # (print(node) for node, out_degree in _G.out_degree() if out_degree == 0)
        # print(is_there_edges(_G))
        # breakpoint()  # DEBUG

    # for item in enumerate(nx.topological_generations(wf.G)):
    #     temp_G = G.copy()
    #     print(item)
    #     breakpoint()  # DEBUG

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

    # https://networkx.org/documentation/stable/auto_examples/drawing/plot_weighted_graph.html
    ##############################################################
    # breakpoint()  # DEBUG
    nx.nx_pydot.write_dot(wf.G, "workflow_job.dot")
    nx.draw_spring(wf.G, with_labels=True)
    plt.savefig("job.png")
    # breakpoint()  # DEBUG
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
