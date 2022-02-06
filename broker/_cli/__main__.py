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


def main():  # noqa
    if args.command == "driver":
        from broker.Driver import main

        main(args)
    elif args.command == "submit":
        from broker.submit_base import SubmitBase

        try:
            base = SubmitBase(args.path)
            base.submit()
        except QuietExit:
            pass
        except Exception as e:
            print_tb(e)
    elif args.command == "daemon":
        if args.daemon_type[0] == "ipfs":
            from broker.utils import run_ipfs_daemon

            run_ipfs_daemon(_is_print=True)
        if args.daemon_type[0] == "slurm":
            from broker.config import env
            from broker.utils import run

            run(["sudo", env.BASH_SCRIPTS_PATH / "run_slurm.sh"])
    elif args.command == "data":
        try:
            cfg.Ebb.get_data_info(args.eth_address)
        except Exception as e:
            print_tb(e)
    elif args.command == "register_provider":
        try:
            cfg.Ebb.register_provider(args.path)
        except Exception as e:
            print_tb(e)
    elif args.command == "register_requester":
        try:
            cfg.Ebb.register_requester(args.path)
        except Exception as e:
            print_tb(e)
    elif args.command == "console":
        import subprocess

        subprocess.call([console_fn])
    else:
        print(f"ebloc-broker v{__version__} - Blockchain based autonomous computational resource broker\n")
        parser.print_help()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
