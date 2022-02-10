#!/usr/bin/env python3

import sys

from broker import cfg
from broker._cli.helper import Helper
from broker._utils.tools import print_tb
from broker.errors import QuietExit

__version__ = "2.0.0"

parser = Helper().get_parser()
args = parser.parse_args()
console_fn = __file__.replace("__main__", "console")


def driver():
    from broker.Driver import main

    main(args)


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
        from broker.utils import run_ipfs_daemon

        run_ipfs_daemon(_is_print=True)
    if args.daemon_type[0] == "slurm":
        from broker.config import env
        from broker.utils import run

        run(["sudo", env.BASH_SCRIPTS_PATH / "run_slurm.sh"])


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


def console():
    import subprocess

    subprocess.call([console_fn])


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
    except:
        print(f"ebloc-broker v{__version__} - Blockchain based autonomous computational resource broker\n")
        parser.print_help()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
