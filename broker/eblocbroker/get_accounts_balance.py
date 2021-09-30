#!/usr/bin/env python3

from os import listdir

import broker.eblocbroker.Contract as Contract
from broker._utils.tools import _colorize_traceback, log
from brownie import accounts


def main():
    Ebb: "Contract.Contract" = Contract.EBB()
    path = "/home/alper/.brownie/accounts"
    dirlist = listdir(path)
    for fname in dirlist:
        account_path = f"{path}/{fname}"
        print(account_path)
        Ebb.brownie_load_account(str(fname), "alper")

    for account in accounts:
        try:
            if str(account) != "0x3e7C819690A79eCB1A5Babf5F9CDe57e3ECA2A22":
                balance = Ebb._get_balance(account)
                log(f"==> {account}={balance} eth")
        except Exception as e:
            _colorize_traceback(e)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        _colorize_traceback(e)
