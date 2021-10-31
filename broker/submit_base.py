#!/usr/bin/env python3

import os
import sys

from broker.config import env
from broker.lib import check_linked_data, log


class SubmitBase:
    def __init__(self):
        pass

    def check_link_folders(self, folders_to_share):
        path_from = env.EBLOCPATH / "base" / "data"
        path_to = env.LINK_PATH / "base" / "data_link"
        check_linked_data(path_from, path_to, folders_to_share[1:])
        for folder in folders_to_share:
            if not os.path.isdir(folder):
                log(f"E: {folder} path does not exist")
                sys.exit(1)
