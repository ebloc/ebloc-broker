import importlib

from contract.scripts import project


def main():
    importlib.reload(project)
    project.project()
