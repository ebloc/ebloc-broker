#!/usr/bin/env python3

from broker.lib import run
from broker.libs.gdrive import delete_all, refresh_gdrive_token
from broker.utils import is_program_valid, print_tb


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
