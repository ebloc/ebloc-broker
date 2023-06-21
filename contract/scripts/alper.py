#!/usr/bin/env python3

import importlib
from contract.scripts import project


def main():
    importlib.reload(project)
    project.project()


if __name__ == "__main__":
    main()
