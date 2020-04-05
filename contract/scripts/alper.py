import importlib

from brownie import *
from scripts import project


def main():
    importlib.reload(project)
    project.project()
