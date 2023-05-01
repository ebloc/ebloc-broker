#!/usr/bin/env python3

import getpass
import git
import os
import sys
from inspect import getsourcefile
from os.path import abspath, expanduser
from pathlib import Path

from broker._utils.yaml import Yaml


def is_docker() -> bool:
    path = "/proc/self/cgroup"
    return os.path.exists("/.dockerenv") or os.path.isfile(path) and any("docker" in line for line in open(path))


def get_git_root(path) -> str:
    git_repo = git.Repo(path, search_parent_directories=True)
    git_root = git_repo.git.rev_parse("--show-toplevel")
    return git_root


def main():
    executed_fn = abspath(getsourcefile(lambda: 0))
    git_root = get_git_root(executed_fn)
    yaml_fn = expanduser("~/.ebloc-broker/cfg.yaml")
    if not os.path.exists(yaml_fn):
        raise Exception(f"E: yaml_fn({yaml_fn}) does not exist")

    home_dir = Path(os.path.expanduser("~"))
    yaml_file = Yaml(yaml_fn)["cfg"]
    yaml_file["whoami"] = getpass.getuser()
    yaml_file["home_dir"] = str(home_dir)
    yaml_file["datadir"] = str(home_dir / ".eblocpoa")
    yaml_file["log_path"] = str(home_dir / ".ebloc-broker")
    yaml_file["ebloc_path"] = git_root
    if is_docker():
        yaml_file["provider"]["slurm_user"] = "slurm"


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
