#!/usr/bin/env python3

import sys

from broker.config import env
from broker.lib import check_linked_data

if __name__ == "__main__":
    path_from = f"{env.EBLOCPATH}/base/data"
    path_to = f"{env.LINK_PATH}/base/data_link"
    check_linked_data(path_from, path_to, is_continue=True)
    sys.exit(0)
