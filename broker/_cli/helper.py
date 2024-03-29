#!/usr/bin/env python3

# PYTHON_ARGCOMPLETE_OK
import argcomplete
import argparse
from argcomplete.completers import EnvironCompleter
from argparse import RawTextHelpFormatter


class Helper:
    """Guide for arguments."""

    def __init__(self):
        """Initialize helper.

        ./broker/_cli/__main__.py -h

        activate-global-python-argcomplete --user
        eval "$(register-python-argcomplete ~/venv/bin/eblocbroker)"

        __ https://github.com/kislyuk/argcomplete/issues/442
        __ https://kislyuk.github.io/argcomplete/
        __ https://stackoverflow.com/a/15289025/2402577
        __ https://docs.python.org/3/library/argparse.html
        __ https://github.com/kislyuk/argcomplete
        __ https://stackoverflow.com/questions/14597466/custom-tab-completion-in-python-argparse
        """
        self.parser = argparse.ArgumentParser(
            "eblocbroker",
            epilog="Type 'eblocbroker <command> --help' for specific options and more information\nabout each command.",
            usage="usage: %(prog)s [-h] command [<options>...]",
            formatter_class=RawTextHelpFormatter,
        )
        self.parser._positionals.title = "Commands"
        self.parser._optionals.title = "Options"
        self.subparsers = self.parser.add_subparsers(dest="command", metavar="command [<options>...]")
        self.subparsers.add_parser("about", help="ebloc-broker metadata")
        self.init()
        self.driver()
        # self.workflow()
        self.run()
        self.daemon()
        # self.register()
        self.submit()
        self.data()
        self.balance()
        self.subparsers.add_parser("providers", help="List of registered providers.")
        self.subparsers.add_parser("console", help="Load the console")
        argcomplete.autocomplete(self.parser)

    def get_args(self):
        return self.parser.parse_args()

    def get_parser(self) -> argparse.ArgumentParser:
        return self.parser

    def init(self):
        obj = self.subparsers.add_parser("init", help="Initialize the ebloc-broker project")
        obj.add_argument(
            "--base", action="store_true", help="Set cfg.py file with initial values"
        ).completer = EnvironCompleter
        obj.set_defaults(is_base=None)

    def driver(self):
        obj = self.subparsers.add_parser("driver", help="Driver program", epilog="run: nohup ebloc-broker > cmd.log &!")
        obj.add_argument(
            "--bn", type=int, default=0, help="Block number to start fetch blocks from"
        ).completer = EnvironCompleter
        obj.add_argument(
            "--latest", action="store_true", help="Block number to start fetch blocks from latest"
        ).completer = EnvironCompleter
        obj.add_argument(
            "--thread", dest="is_thread", action="store_true", help="Enables threading"
        ).completer = EnvironCompleter
        obj.add_argument(
            "--no-thread", dest="is_thread", action="store_false", help="Disables threading"
        ).completer = EnvironCompleter
        obj.set_defaults(is_thread=None)

    def run(self):
        """Run scripts.

        __ https://stackoverflow.com/a/50965772/2402577
        """
        obj = self.subparsers.add_parser("run", help="Run a script in the eblocbroker_scripts/ folder")
        obj.add_argument(
            "--tx-receipt", type=str, metavar="[tx_hash]", help="Return Transaction Receipt"
        ).completer = EnvironCompleter
        obj.add_argument(
            "--authenticate-orcid",
            type=str,
            nargs=2,
            metavar=("[eth_address]", "[oricd]"),
            action="append",
            help="Authenticate orcid",
        ).completer = EnvironCompleter
        #
        obj.add_argument(
            "--register-provider",
            type=str,
            metavar="[file.yaml]",
            help="Register provider.",
        ).completer = EnvironCompleter
        obj.add_argument(
            "--register-requester",
            type=str,
            metavar="[file.yaml]",
            help="Register requester.",
        ).completer = EnvironCompleter

    # def workflow(self):
    #     obj = self.subparsers.add_parser("workflow", help="eblocworkflow scripts")  # noqa

    def daemon(self):
        """Select daemon program to run.

        __ https://stackoverflow.com/a/40324928/2402577
        """
        obj = self.subparsers.add_parser("daemon", help="Daemon scripts")
        obj.add_argument(
            "daemon_type",
            # default="all",
            # const="all",
            nargs=1,
            choices=["ipfs", "slurm"],
            help="Select program to run as a daemon on the background",
        )

    def submit(self):
        obj = self.subparsers.add_parser("submit", help="Submit job")
        obj.add_argument("path", type=str, help="Full file path of Yaml file that contains the job info")
        # obj.add_argument('path', nargs='+', help='Full file path of Yaml file that contains the job info')

    def data(self):
        obj = self.subparsers.add_parser("data", help="List registered data files of the provider")
        obj.add_argument("eth_address", type=str, help="Ethereum address of the provider")

    def balance(self):
        # FIXME: return balance and convert it into usd
        obj = self.subparsers.add_parser("balance", help="Returns user's earned money amount in USD token.")
        obj.add_argument("eth_address", type=str, help="Ethereum address of the provider")


# def register(self):
#     register_provider = self.subparsers.add_parser("register_provider", help="Register provider")
#     register_provider.add_argument(
#         "path", type=str, help="Full file path of Yaml file that contains the provider info"
#     )
#     register_requester = self.subparsers.add_parser("register_requester", help="Register requester")
#     register_requester.add_argument(
#         "path", type=str, help="Full file path of Yaml file that contains the requester info"
#     )

# parser.add_argument(
#     '--debug',
#     action='store_true',
#     help='Print debug info'
# )
# driver.add_argument('name', nargs='+', help='name(s) to driver')
#
# submit.add_argument(
#     'reason',
#     help='what to submit for (optional)',
#     default="no reason",
#     nargs='?'
# )
# parser.add_argument("bar", nargs="*", default=[1, 2, 3], help="BAR!")

# if args.debug:
#     print("debug: " + str(args))

# if not (args.driver or args.upload):
#     parser.error('No action requested, add -process or -upload')
#
# parser.add_argument("bar", nargs="*", default=[1, 2, 3], help="BAR!")
