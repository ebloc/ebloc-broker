#!/usr/bin/env python3

import os
import sys
from typing import Dict

from broker._utils.tools import log, mkdir, run
from broker.config import env
from broker.utils import generate_md5sum, path_leaf, question_yes_no


class Link:
    def __init__(self, path_from, path_to) -> None:
        self.data_map = {}  # type: Dict[str, str]
        self.path_from = path_from
        self.path_to = path_to

    def link_folders(self, paths=None):
        """Create linked folders under the data_link folder."""
        from os import listdir
        from os.path import isdir, join

        if not paths:
            # instead of full path only returns folder names
            paths = [f for f in listdir(self.path_from) if isdir(join(self.path_from, f))]
            is_only_folder_names = True
        else:
            is_only_folder_names = False

        for idx, path in enumerate(paths):
            if is_only_folder_names:
                folder_name = path
                path = f"{self.path_from}/{path}"
            else:
                folder_name = path_leaf(path)

            try:
                folder_hash = generate_md5sum(path)
            except Exception as e:
                raise e

            self.data_map[folder_name] = folder_hash
            destination = f"{self.path_to}/{folder_hash}"
            run(["ln", "-sfn", path, destination])

            log(f" ┌── {path}", "bold green")
            log(f" └─> {destination}", "bold yellow")
            if idx < len(paths) - 1:
                log()

            folder_new_hash = generate_md5sum(destination)
            assert folder_hash == folder_new_hash, "Hash does not match original and linked folder"


def check_link_folders(folders_to_share):
    path_to = env.LINK_PATH / "base" / "data_link"
    check_linked_data(folders_to_share, path_to)
    for folder in folders_to_share:
        if not os.path.isdir(folder):
            log(f"E: {folder} path does not exist")


def check_linked_data(paths_from, path_to, is_continue=False):
    """Generate folder as hard linked of the given folder paths or provider main folder.

    :param paths_from: iterates all over the given folders
    :param path_to: linked folders_to_share into into given path
    """
    mkdir(path_to)
    link = Link(paths_from, path_to)
    link.link_folders(paths_from)
    log()
    for key, value in link.data_map.items():
        log(f"[bold green] * {key}[/bold green] => [bold yellow]../data_link/{value}[/bold yellow]")

    if not is_continue:
        print("")
        question_yes_no(
            "#> Would you like to continue with linked folder path in your run.sh?\n"
            "If no, please feel free to update your run.sh file and continue"
        )

    for folder in paths_from:
        if not os.path.isdir(folder):
            log(f"E: {folder} path does not exist")
            sys.exit(1)


if __name__ == "__main__":
    path_from = env.HOME / "test_eblocbroker" / "test_data" / "base" / "data"
    path_to = env.LINK_PATH / "base" / "data_link"
    check_linked_data(path_from, path_to, is_continue=True)
