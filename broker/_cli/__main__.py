#!/usr/bin/env python3

import sys

from broker import cfg
from broker._cli.helper import Helper
from broker._utils.tools import print_tb
from broker.errors import QuietExit

helper = Helper()
parser = helper.get_parser()
args = parser.parse_args()
console_fn = __file__.replace("__main__", "console")


def driver():
    from broker.Driver import main

    main(args)


def init():
    import git
    from pathlib import Path
    from broker._utils.tools import run_keep_print

    f = Path(__file__).parent.resolve()
    repo = git.Repo(f, search_parent_directories=True)
    run_keep_print(Path(repo.working_tree_dir) / "broker" / "bash_scripts" / "folder_setup.sh")


def about():
    from os.path import expanduser

    from broker._utils._log import log

    with open(expanduser("~/.ebloc-broker/cfg.yaml"), "r") as f:
        flag = True
        indent = 2
        for line in f:
            if flag:
                if "  " in line[:2]:
                    flag = False
                    if "    " in line[:4]:
                        indent = 4

            if "cfg" not in line and " " * indent in line[:indent]:
                line = line[indent:]
                log(line.rstrip(), "bold")


def daemon():
    if args.daemon_type[0] == "ipfs":
        from broker.utils import start_ipfs_daemon

        start_ipfs_daemon(_is_print=True)
    if args.daemon_type[0] == "slurm":
        import git
        import pathlib
        from broker._utils.tools import run_keep_print

        f = pathlib.Path(__file__).parent.resolve()
        repo = git.Repo(f, search_parent_directories=True)
        run_keep_print(repo.working_tree_dir / "broker" / "bash_scripts" / "run_slurm.sh")


def console():
    import subprocess

    subprocess.call([console_fn])


def providers():
    from broker._utils._log import log

    try:
        providers = cfg.Ebb.get_providers()
        if len(providers) == 0:
            log("warning: there is no registered provider")
        else:
            for provider in providers:
                log(provider.lower())
    except Exception as e:
        print_tb(e)


def register_provider():
    try:
        cfg.Ebb.register_provider(args.path)
    except Exception as e:
        print_tb(e)


def register_requester():
    try:
        cfg.Ebb.register_requester(args.path)
    except Exception as e:
        print_tb(e)


def data():
    try:
        cfg.Ebb.get_data_info(args.eth_address)
    except Exception as e:
        print_tb(e)


def withdraw():
    try:
        cfg.Ebb.withdraw(args.eth_address)
    except Exception as e:
        print_tb(e)


def balance():
    from broker._utils._log import log

    try:
        balance = cfg.Ebb.get_balance(args.eth_address)
        log(f"## balance={balance}")
    except Exception as e:
        print_tb(e)


def submit():
    from broker.submit_base import SubmitBase

    try:
        base = SubmitBase(args.path)
        base.submit()
    except QuietExit:
        pass
    except Exception as e:
        print_tb(e)


def main():  # noqa
    try:
        globals()[args.command]()
    except KeyError:
        print(f"ebloc-broker v{cfg.__version__} - Blockchain based autonomous computational resource broker\n")
        parser.print_help()
    except Exception as e:
        print_tb(e)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
