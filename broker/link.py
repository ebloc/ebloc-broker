#!/usr/bin/env python3

from broker.config import env
from broker.lib import check_linked_data

if __name__ == "__main__":
    path_from = env.HOME / "test_eblocbroker" / "test_data" / "base" / "data"
    path_to = env.LINK_PATH / "base" / "data_link"
    check_linked_data(path_from, path_to, is_continue=True)
