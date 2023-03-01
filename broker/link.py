#!/usr/bin/env python3

import os
import sys
from contextlib import suppress
from pathlib import Path
from typing import Dict  # noqa

from broker import cfg
from broker._utils.tools import log, mkdir, run
from broker.config import env
from broker.utils import generate_md5sum, path_leaf, question_yes_no


class Link:
    def __init__(self, folder_target, folder_link) -> None:
        self.data_map = {}  # type: Dict[str, str]
        self.folder_target = folder_target
        self.folder_link = folder_link

    def umount(self, data_hashes) -> None:
        for data_hash in data_hashes:
            if isinstance(data_hash, bytes):
                data_hash = data_hash.decode("utf-8")

            dest = f"{self.folder_link}/{data_hash}"
            if os.path.isdir(dest):
                with suppress(Exception):
                    run(["sudo", "umount", "-f", dest], is_quiet=True)

    def link(self, path, dest, is_read_only=False):
        """Make link between folders.

        You can create a read-only bind-mount(https://lwn.net/Articles/281157/)
        mount --bind /path/to/source/ /path/to/dest/
        mount -o bind,remount,ro /path/to/dest

        __ https://askubuntu.com/a/243390/660555
        """
        if is_read_only:
            mkdir(dest)
            run(["sudo", "mount", "--bind", path, dest])
            run(["sudo", "mount", "-o", "bind,remount,ro", dest])
        else:
            run(["ln", "-sfn", path, dest])

        log(f" ┌── {path}", "bold green")
        log(f" └─> {dest}", "bold yellow")

    def registered_data(self, data_hashes):
        for data_hash in data_hashes:
            if isinstance(data_hash, bytes):
                data_hash = data_hash.decode("utf-8")

            self.link(
                Path("/") / "var" / "ebloc-broker" / "cache" / data_hash,
                f"{self.folder_link}/{data_hash}",
                is_read_only=True,
            )

    def link_folders(self, paths=None):
        """Create linked folders under the data_link folder."""
        from os import listdir
        from os.path import isdir, join

        if paths:
            is_only_folder_names = False
        else:
            # instead of full path only returns folder names
            paths = [f for f in listdir(self.folder_target) if isdir(join(self.folder_target, f))]
            is_only_folder_names = True

        for idx, path in enumerate(paths):
            if not isinstance(path, bytes):
                if is_only_folder_names:
                    folder_name = path
                    path = f"{self.folder_target}/{path}"
                else:
                    folder_name = path_leaf(path)

                try:
                    folder_hash = generate_md5sum(path)
                except Exception as e:
                    raise e

                self.data_map[folder_name] = folder_hash
                dest = f"{self.folder_link}/{folder_hash}"
                self.link(path, dest)
                if idx < len(paths) - 1:
                    log()

                folder_new_hash = generate_md5sum(dest)
                assert folder_hash == folder_new_hash, "Hash of the original and the linked folder does not match"


def check_link_folders(folders_to_share, registered_data_files, source_code_path, is_pass=False):
    is_continue = False
    if registered_data_files:
        is_continue = True
        for data_file in registered_data_files:
            if isinstance(data_file, bytes):
                data_file = data_file.decode("utf-8")

            log(f"[blue] * [/blue][green]{data_file}[/green] => [yellow]../data_link/{data_file}[/yellow]", "bold")

    if folders_to_share:
        is_continue = True
        folder_link = env.LINK_PATH / "base" / "data_link"
        check_linked_data(folders_to_share, folder_link, source_code_path, is_pass)
        for folder in folders_to_share:
            if not os.path.isdir(folder):
                log(f"E: {folder} path does not exist")
    elif is_continue:
        print()
        if not is_pass:
            question_yes_no(
                "#> Would you like to continue with linked folder path in your `[m]run.sh[/m]` file?\n"
                "If no, please feel free to update your run.sh file and continue",
                is_exit=True,
            )


def test_with_small_dataset(value):
    fn = os.path.expanduser("~/test_eblocbroker/run_cppr/run.sh")
    with open(fn, "r+") as file:
        file_data = file.read()

    changed_file_data = file_data.replace("DATA_HASH='change_folder_hash'", f"DATA_HASH='{value}'")
    with open(fn, "w+") as file:
        file.write(changed_file_data)


def check_linked_data(folders_target, folder_link, source_code_path="", is_pass=False):
    """Generate folder as hard linked of the given folder paths or provider main folder.

    :param folders_target: iterates all over the given folders
    :param folder_link: linked folders_to_share into into given path
    """
    mkdir(folder_link)
    link = Link(folders_target, folder_link)
    link.link_folders(folders_target)
    log()
    for key, value in link.data_map.items():
        # test_with_small_dataset(value)  # delete_me
        log(f"[blue] * [/blue][green]{key}[/green] => [yellow]../data_link/{value}[/yellow]", "bold")

    if not is_pass:
        print("")
        question_yes_no(
            "#> Would you like to continue with the linked folder path in your `[m]run.sh[/m]` file?\n"
            "If no, feel free to update your run.sh file and continue",
            is_exit=True,
        )

    for folder in folders_target:
        if not os.path.isdir(folder):
            log(f"E: {folder} path does not exist")
            sys.exit(1)

    if is_pass and cfg.IS_FULL_TEST and "run_cppr" in str(source_code_path):
        for key, value in link.data_map.items():
            test_with_small_dataset(value)  # delete_me


def main():
    folder_target = env.HOME / "test_eblocbroker" / "test_data" / "base" / "data"
    folder_link = env.LINK_PATH / "base" / "data_link"
    check_linked_data(folder_target, folder_link, is_pass=True)


if __name__ == "__main__":
    main()
