#!/usr/bin/env python3

import os

from config import EBLOCPATH
from utils import Link, create_dir

if __name__ == "__main__":
    try:
        cwd = os.path.dirname(os.path.abspath(__file__))
    except Exception:
        cwd = os.getcwd()

    path_from = f"{EBLOCPATH}/base/data"
    path_to = f"{EBLOCPATH}/base/data_link"

    create_dir(path_to)

    link = Link(path_from, path_to)
    link.link_folders()

    for key, value in link.data_map.items():
        print(f"{key} => data_link/{value}")

    exit(0)
