#!/usr/bin/env python3

from lib import check_linked_data
from settings import init_env
from utils import Link, create_dir

env = init_env()

if __name__ == "__main__":
    path_from = f"{env.EBLOCPATH}/base/data"
    path_to = f"{env.EBLOCPATH}/base/data_link"

    check_linked_data(path_from, path_to)
    """
    create_dir(path_to)

    link = Link(path_from, path_to)
    link.link_folders()

    for key, value in link.data_map.items():
        print(f"{key} => data_link/{value}")
    """
    exit(0)
