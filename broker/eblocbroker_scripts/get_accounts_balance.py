#!/usr/bin/env python3

from os import listdir
from os.path import expanduser

from broker import cfg
from broker._utils.tools import log, print_tb
from brownie import accounts


def main():
    Ebb = cfg.Ebb
    path = expanduser("~/.brownie/accounts")
    dirlist = listdir(path)
    for fname in dirlist:
        account_path = f"{path}/{fname}"
        print(account_path)
        Ebb.brownie_load_account(str(fname), "alper")

    sum_balance = 0
    for account in accounts:
        try:
            if str(account) != "0x3e7C819690A79eCB1A5Babf5F9CDe57e3ECA2A22":
                balance = Ebb._get_balance(account)
                log(f"==> [yellow]{str(account).lower()}[/yellow]={balance} eth")
                sum_balance += balance
        except Exception as e:
            print_tb(e)

    log(f"==> total_balance={sum_balance}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print_tb(e)
