#!/usr/bin/env python3

from broker._utils.tools import print_tb
from broker.errors import QuietExit
from broker.helper import helper

parser = helper()
args = parser.parse_args()


def main():
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
    else:
        __version__ = "1.0.0"
        print(f"ebloc-broker v{__version__} - Blockchain based autonomous computational resource broker\n")
        parser.print_help()


if __name__ == "__main__":
    main()
