#!/usr/bin/env python3

import matplotlib.pyplot as plt
import networkx as nx
import random
from typing import List

from broker._utils._log import console, log
from broker._utils.tools import print_tb, run
from broker.errors import QuietExit


class Workflow:
    """Object to access ebloc-broker smart-contract functions."""

    def __init__(self, G=None) -> None:
        self.job_ids = {}  # type: ignore
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

    def topological_generations(self) -> List:
        """Take all the nodes in the DAG that don’t have any dependencies and put them in list.
        “Remove” those nodes from the DAG.
        Repeat the process, creating a new list at each step.
        Thus, topological sorting is reduced to correctly stratifying the graph in this way.

        __ https://networkx.org/nx-guides/content/algorithms/dag/index.html
        """
        return list(nx.topological_generations(self.G))

    def bfs_layers(self, _list) -> dict:
        """BFS Layers.

        __ https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.traversal.breadth_first_search.bfs_layers.html
        """
        return dict(enumerate(nx.bfs_layers(self.G, _list)))

    def write_dot(self, fn="output.dot"):
        """Create digraph."""

        nx.nx_pydot.write_dot(self.G, fn)

    def read_dot(self, fn="job.dot") -> None:
        """Create digraph."""
        self.G = nx.drawing.nx_pydot.read_dot(fn)

    def print_predecessors(self):
        for i in list(self.G.nodes):
            print(f"{set(self.G.predecessors(i))} => {i}")

    def draw(self):
        try:
            nx.draw_networkx(self.G, **self.options)
            plt.savefig("output.png")
            ax = plt.gca()
            ax.margins(0.20)
            plt.axis("off")
            plt.show()
        except KeyboardInterrupt:
            pass

    def dependency_job(self, i, slurm=False):
        if not len(set(self.G.predecessors(i))):
            job_id = self.not_dependent_submit_job(i, slurm)
            self.job_ids[i] = job_id
            print("job_id: " + str(job_id))
        else:
            job_id = self.dependent_submit_job(i, list(self.G.predecessors(i)), slurm)
            self.job_ids[i] = job_id
            print("job_id: " + str(job_id))
            print(list(self.G.predecessors(i)))

    def not_dependent_submit_job(self, i, slurm):
        log(f"$ sbatch job{i}.sh", "pink")
        if slurm:
            cmd = ["sbatch", f"job{i}.sh"]
            output = run(cmd)
            print(output)
            job_id = int(output.split(" ")[3])
            return job_id
        else:
            return random.randint(1, 101)

    def dependent_submit_job(self, i, predecessors, slurm):
        if len(predecessors) == 1:
            if not predecessors[0] in self.job_ids:
                #: if the required job is not submitted to Slurm, recursive call
                self.dependency_job(predecessors[0])

            log(f"$ sbatch --dependency=afterok:{self.job_ids[predecessors[0]]} job{i}.sh", "blue")
            if slurm:
                cmd = ["sbatch", f"--dependency=afterok:{self.job_ids[predecessors[0]]}", f"job{i}.sh"]
                output = run(cmd)
                print(output)
                job_id = int(output.split(" ")[3])
                return job_id
            else:
                return random.randint(1, 101)
        else:
            job_id_str = ""
            for j in predecessors:
                if j not in self.job_ids:  # if the required job is not submitted to Slurm, recursive call
                    self.dependency_job(j)

                job_id_str += f"{self.job_ids[j]}:"

            job_id_str = job_id_str[:-1]
            log(f"$ sbatch --dependency=afterok:{job_id_str} job{i}.sh", "blue")
            if slurm:
                cmd = ["sbatch", f"--dependency=afterok:{job_id_str}", f"job{i}.sh"]
                output = run(cmd)
                print(output)
                job_id = int(output.split(" ")[3])
                return job_id
            else:
                return random.randint(1, 101)

    def generate_random_dag(self, number_nodes, number_edges):
        G = nx.DiGraph()
        while G.number_of_edges() < number_edges:
            start_node, end_node = random.sample(range(number_nodes), 2)
            #: ensure that node 0 is always a source (initial node)
            if end_node == 0:
                start_node, end_node = end_node, start_node

            G.add_edge(start_node, end_node)
            if not nx.is_directed_acyclic_graph(G):
                G.remove_edge(start_node, end_node)

        return G


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


def test_3():
    G = nx.Graph(directed=True)
    # G.add_edges_from([(0, 5), (1, 5), (2, 5), (3, 5), (4, 5), (6, 0), (7, 0), (8, 7), (9, 7)])
    G.add_edges_from([(0, 1), (0, 2), (0, 3), (0, 4), (1, 5), (2, 5), (3, 5), (4, 5)])
    w = Workflow(G)
    w.write_dot()
    w.draw()


def test_4(slurm=False):
    G = nx.DiGraph()
    G.add_edge(0, 1)
    G.add_edge(0, 2)
    G.add_edge(1, 3)
    G.add_edge(2, 3)
    # G.add_edge(9, 7, weight=10)  # example

    # jobs
    # G.add_edges_from([(0, 5), (1, 5), (2,5), (3,5), (4,5), (6,0), (7,0), (8,7), (9,7)])
    # G is:
    # 0 -> 5  6 -> 0  8 -> 7
    # 1 -> 5  7 -> 0  9 -> 7
    # 2 -> 5
    # 3 -> 5
    # 4 -> 5
    nx.nx_pydot.write_dot(G, "job.dot")  # saves DAG into job.dot file

    w = Workflow()
    w.read_dot("job.dot")
    # log(f"List of nodes={list(w.G.nodes)}")
    for idx in list(w.G.nodes):
        depended_nodes = set(w.G.predecessors(idx))
        if idx != "\\n" and depended_nodes:
            print(f"{idx} => {depended_nodes}")

    print()
    for idx in list(w.G.nodes):
        if idx != "\\n" and idx not in w.job_ids:
            w.dependency_job(idx, slurm=slurm)

    # for idx in list(G.nodes):
    #     print(idx + " " + str(job_ids[idx]))

    # jid4=$(sbatch --dependency=afterany:$jid2:$jid3 job4.sh)


def test_5():
    G = nx.DiGraph(directed=True)
    edges = [
        ("m", "r"),
        ("m", "q"),
        ("m", "x"),
        ("n", "o"),
        ("n", "u"),
        ("n", "q"),
        ("o", "r"),
        ("o", "v"),
        ("o", "s"),
        ("p", "o"),
        ("p", "s"),
        ("p", "z"),
        ("v", "w"),
        ("v", "x"),
        ("r", "u"),
        ("r", "y"),
        ("s", "r"),
        ("u", "t"),
        ("w", "z"),
    ]
    G.add_edges_from(edges)
    w = Workflow(G)
    w.print_predecessors()
    print(w.topological_sort())
    # w.draw()
    # sol: p; n; o; s; m; r; y; v; x; w; ´; u; q; t.


if __name__ == "__main__":
    try:
        # test_0()
        # test_1()
        # test_2()
        # test_3()
        test_4()
        # test_4(slurm=True)
        # test_5()
    except KeyboardInterrupt:
        pass
    except QuietExit as e:
        print(f"==> {e}")
    except Exception as e:
        print_tb(str(e))
        console.print_exception(word_wrap=True)
