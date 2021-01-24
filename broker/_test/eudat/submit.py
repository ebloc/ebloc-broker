#!/usr/bin/env python3

import sys

import libs.eudat as eudat
from config import env
from imports import connect
from utils import _colorize_traceback


def main():
    connect()
    oc_requester = "059ab6ba-4030-48bb-b81b-12115f531296"
    provider = "0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49"  # home2-vm
    account_id = 1  # different account-id than the provider if test is in the same VM

    eudat.login(oc_requester, f"{env.LOG_PATH}/.eudat_client.txt", env.OC_CLIENT_REQUESTER)

    base_dir = f"{env.HOME}/test_eblocbroker"
    source_code_dir = f"{base_dir}/source_code"
    data_1_dir = f"{base_dir}/datasets/BL06-camel-sml"

    folders_to_share = []  # full path of the code or data should be provided
    folders_to_share.append(source_code_dir)
    folders_to_share.append(data_1_dir)
    eudat.submit(provider, account_id, folders_to_share)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        if type(e).__name__ != "KeyboardInterrupt":
            _colorize_traceback()
        sys.exit(1)
