#!/usr/bin/env python3

import argparse
from argparse import RawTextHelpFormatter


def helper():
    """Guide for arguments."""
    parser = argparse.ArgumentParser(
        "eblocbroker.py",
        epilog="""Type 'eblocbroker.py <command> --help' for specific options and more information\nabout each command.""",
        formatter_class=RawTextHelpFormatter,
        usage="usage: %(prog)s [-h] command [<options>...]",
    )
    parser._positionals.title = "Commands"
    parser._optionals.title = "Options"
    subparsers = parser.add_subparsers(dest="command", metavar="command [<options>...]")
    driver = subparsers.add_parser(
        "driver", help="Driver script for provider", epilog="run: nohup ebloc-broker > cmd.log &!"
    )
    driver.add_argument("--bn", type=int, default=0, help="Block number to start fetch blocks from")
    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    submit = subparsers.add_parser("submit", help="Submit job")
    submit.add_argument("path", type=str, help="Full file path of Yaml file that contains the job info")
    # submit.add_argument('path', nargs='+', help='Full file path of Yaml file that contains the job info')
    return parser


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
