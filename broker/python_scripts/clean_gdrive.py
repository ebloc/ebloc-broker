#!/usr/bin/env python3

from broker.lib import run
from broker.libs.gdrive import delete_all
from broker.utils import is_program_valid, print_tb
from broker.libs.gdrive import refresh_gdrive_token


def main():
    try:
        is_program_valid(["gdrive", "version"])
        refresh_gdrive_token()
        run(["gdrive", "about"])
    except Exception as e:
        print_tb(e)
        raise e

    delete_all()


if __name__ == "__main__":
    main()
