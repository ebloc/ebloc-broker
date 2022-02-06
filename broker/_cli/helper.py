#!/usr/bin/env python3

# PYTHON_ARGCOMPLETE_OK
import argcomplete
import argparse
from argcomplete.completers import EnvironCompleter
from argparse import RawTextHelpFormatter


# TODO: https://github.com/kislyuk/argcomplete
class Helper:
    """Guide for arguments."""

    def __init__(self):
        self.parser = argparse.ArgumentParser(
            "eblocbroker.py",
            epilog="Type 'eblocbroker <command> --help' for specific options and more information\nabout each command.",
            usage="usage: %(prog)s [-h] command [<options>...]",
            formatter_class=RawTextHelpFormatter,
        )
        argcomplete.autocomplete(self.parser)
        self.parser._positionals.title = "Commands"
        self.parser._optionals.title = "Options"
        self.subparsers = self.parser.add_subparsers(dest="command", metavar="command [<options>...]")
        self._driver()
        self._submit()
        self._daemon()
        self._register()
        self._data()
        self.subparsers.add_parser("console", help="Load the console")
        argcomplete.autocomplete(self.parser)

    def get_parser(self) -> argparse.ArgumentParser:
        return self.parser

    def _driver(self):
        driver = self.subparsers.add_parser(
            "driver", help="Driver scripts", epilog="run: nohup ebloc-broker > cmd.log &!"
        )
        driver.add_argument("--bn", type=int, default=0, help="Block number to start fetch blocks from")
        driver.add_argument("--latest", action="store_true", help="Block number to start fetch blocks from latest")
        driver.add_argument("--thread", dest="is_thread", action="store_true", help="Enables threading")
        driver.add_argument("--no-thread", dest="is_thread", action="store_false", help="Disables threading")
        driver.set_defaults(is_thread=None)

    def _daemon(self):
        """Select daemon program to run.

        __ https://stackoverflow.com/a/40324928/2402577
        """
        daemon = self.subparsers.add_parser("daemon", help="Daemon scripts")
        daemon.add_argument(
            "daemon_type",
            # default="all",
            # const="all",
            nargs=1,
            choices=["ipfs", "slurm"],
            help="Select program to run as a daemon on the background",
        )

    def _submit(self):
        submit = self.subparsers.add_parser("submit", help="Submit job")
        submit.add_argument("path", type=str, help="Full file path of Yaml file that contains the job info")
        # submit.add_argument('path', nargs='+', help='Full file path of Yaml file that contains the job info')

    def _register(self):
        register_provider = self.subparsers.add_parser("register_provider", help="Register provider")
        register_provider.add_argument(
            "path", type=str, help="Full file path of Yaml file that contains the provider info"
        )
        register_requester = self.subparsers.add_parser("register_requester", help="Register requester")
        register_requester.add_argument(
            "path", type=str, help="Full file path of Yaml file that contains the requester info"
        )

    def _data(self):
        data = self.subparsers.add_parser("data", help="List registered data files of the provider")
        data.add_argument("eth_address", type=str, help="Ethereum address of the provider")


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
