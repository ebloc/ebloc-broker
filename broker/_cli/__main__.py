#!/usr/bin/env python3

import sys

from broker import cfg
from broker._cli.helper import Helper
from broker._utils.tools import print_tb
from broker.errors import QuietExit

try:
    helper = Helper()
    parser = helper.get_parser()
    _args = parser.parse_args()
    console_fn = __file__.replace("__main__", "console")
except KeyboardInterrupt:
    sys.exit(1)


def driver():
    from broker.Driver import main

    try:
        main(_args)
    except KeyboardInterrupt:
        sys.exit(1)


def workflow():
    from broker.workflow import Workflow

    try:
        Workflow.main(_args)
    except KeyboardInterrupt:
        sys.exit(1)


def init():
    import git
    from pathlib import Path

    from broker._utils.tools import constantly_print_popen

    try:
        fn = Path(__file__).parent.resolve()
        repo = git.Repo(fn, search_parent_directories=True)
        arg1 = ""
        if _args.base:
            arg1 = "base"

        fn = Path(repo.working_tree_dir) / "broker" / "bash_scripts" / "folder_setup.sh"
        constantly_print_popen([fn, arg1])
    except KeyboardInterrupt:
        sys.exit(1)


def about():
    from os.path import expanduser

    from broker._utils._log import log

    try:
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
                    log(line.rstrip(), is_write=False)
    except KeyboardInterrupt:
        sys.exit(1)


def run():
    if _args.tx_receipt:
        from broker.eblocbroker_scripts.get_transaction_receipt import get_transaction_receipt

        get_transaction_receipt(_args.tx_receipt)
    elif _args.authenticate_orcid:
        from broker._utils.web3_tools import get_tx_status

        Ebb = cfg.Ebb
        owner_address = Ebb.get_owner()
        address = _args.authenticate_orcid[0]
        orcid = _args.authenticate_orcid[1]
        tx_hash = Ebb.authenticate_orc_id(address, orcid, owner_address)
        if tx_hash:
            get_tx_status(tx_hash)
    elif _args.register_provider:
        try:
            cfg.Ebb.register_provider(_args.register_provider)
        except Exception as e:
            print_tb(e)
    elif _args.register_requester:
        try:
            cfg.Ebb.register_provider(_args.register_requester)
        except Exception as e:
            print_tb(e)


def daemon():
    if _args.daemon_type[0] == "ipfs":
        from broker.utils import start_ipfs_daemon

        try:
            start_ipfs_daemon(_is_print=True)
        except KeyboardInterrupt:
            sys.exit(1)

    if _args.daemon_type[0] == "slurm":
        import git
        import pathlib

        from broker._utils.tools import constantly_print_popen

        try:
            f = pathlib.Path(__file__).parent.resolve()
            repo = git.Repo(f, search_parent_directories=True)
            constantly_print_popen(repo.working_tree_dir / "broker" / "bash_scripts" / "run_slurm.sh")
        except KeyboardInterrupt:
            sys.exit(1)


def console():
    import subprocess

    try:
        subprocess.call([console_fn])
    except KeyboardInterrupt:
        sys.exit(1)


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


def tx_receipt():
    from broker.eblocbroker_scripts.get_transaction_receipt import get_transaction_receipt

    get_transaction_receipt(_args.transaction_hash)


# def register_provider():
#     try:
#         cfg.Ebb.register_provider(_args.path)
#     except Exception as e:
#         print_tb(e)


# def register_requester():
#     try:
#         cfg.Ebb.register_requester(_args.path)
#     except Exception as e:
#         print_tb(e)


def data():
    try:
        cfg.Ebb.get_data_info(_args.eth_address)
    except Exception as e:
        print_tb(e)


def balance():
    from broker._utils._log import log

    try:
        balance = cfg.Ebb.get_balance(_args.eth_address)
        log(f"==> balance={balance}")
    except Exception as e:
        print_tb(e)


def submit():
    from broker.submit_base import SubmitBase

    try:
        base = SubmitBase(_args.path)
        base.submit()
    except QuietExit:
        pass
    except Exception as e:
        print_tb(e)


def get_tag_version() -> str:
    from subprocess import check_output

    __version__ = check_output(["git", "describe", "--tags", "--abbrev=0"])
    return __version__.decode("utf-8").replace("\n", "")


def main():  # noqa
    try:
        globals()[_args.command]()
    except KeyError:
        print(f"ebloc-broker {get_tag_version()} - Blockchain based autonomous computational resource broker\n")
        parser.print_help()
    except Exception as e:
        print_tb(e)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
