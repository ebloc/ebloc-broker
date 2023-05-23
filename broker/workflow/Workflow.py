#!/usr/bin/env python3

import matplotlib.pyplot as plt
import networkx as nx
from typing import List

from broker._utils._log import console, log
from broker._utils.tools import print_tb
from broker.errors import QuietExit


class Base:
    """Import base functions."""

    pass


class Workflow(Base):
    """Object to access ebloc-broker smart-contract functions."""

    def __init__(self, G=None) -> None:
        self.G = G
        self.options = {
            "node_color": "lightblue",
            "node_size": 250,
            "width": 1,
            "arrowstyle": "-|>",
            "arrowsize": 12,
            "with_labels": True,
            "arrows": True,
        }

    def topological_sort(self) -> List:
        return list(nx.topological_sort(self.G))

    def bfs_layers(self, _list) -> dict:
        """BFS Layers.

        __ https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.traversal.breadth_first_search.bfs_layers.html
        """
        return dict(enumerate(nx.bfs_layers(self.G, _list)))

    def draw(self):
        try:
            nx.draw_networkx(self.G, **self.options)
            ax = plt.gca()
            ax.margins(0.20)
            plt.axis("off")
            plt.show()
        except KeyboardInterrupt:
            pass


def main(args):
    try:
        print("here")
        # args
        w = Workflow()  # noqa
    except Exception as e:
        print_tb(e, is_print_exc=False)
        console.print_exception(word_wrap=True, extra_lines=1)
    except KeyboardInterrupt:
        pass


def test_0():
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

    w = Workflow(G)
    w.draw()


def test_1():
    G = nx.DiGraph(directed=True)
    edges = [("A", "D"), ("B", "D"), ("C", "D"), ("A", "E"), ("B", "E"), ("C", "E"), ("D", "F"), ("E", "F")]
    G.add_edges_from(edges)
    log(nx.to_dict_of_dicts(G))
    w = Workflow(G)
    print(w.topological_sort())
    print(w.bfs_layers(["A"]))
    w.draw()


def test_2():
    G = nx.Graph(directed=True)
    G.add_edges_from([(0, 1), (0, 2), (1, 3), (1, 4), (2, 5), (2, 6)])
    w = Workflow(G)
    print(w.bfs_layers([1]))
    print(w.bfs_layers([1, 6]))
    # print(w.topological_sort())


if __name__ == "__main__":
    try:
        # test_0()
        test_1()
        test_2()
    except KeyboardInterrupt:
        pass
    except QuietExit as e:
        print(f"#> {e}")
    except Exception as e:
        print_tb(str(e))
        console.print_exception(word_wrap=True)
