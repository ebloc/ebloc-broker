#!/usr/bin/env python3

from os.path import expanduser
from pathlib import Path

from broker import cfg
from broker._utils.tools import log
from broker.test_setup.user_set import users  # , extra_users

collect_account = "0xfd0ebcd42d4c4c2a2281adfdb48177454838c433".lower()

providers = [
    "0x3e6FfC5EdE9ee6d782303B2dc5f13AFeEE277AeA",
    "0x765508fc8f78a465f518ae79897d0e4b249e82dc",
    "0x38cc03c7e2a7d2acce50045141633ecdcf477e9a",
    "0xeab50158e8e51de21616307a99c9604c1c453a02",
]

Ebb = cfg.Ebb
_collect_account = collect_account.replace("0x", "")
fname = str(Path(expanduser("~/.brownie/accounts")) / _collect_account)
_collect_account = Ebb.brownie_load_account(fname, "alper")
log(f"collect_account={Ebb._get_balance(collect_account)}", "bold")


def collect_all_into_base():
    for account in users:
        _account = account.lower().replace("0x", "")
        fname = Path(expanduser("~/.brownie/accounts")) / _account
        print(fname)
        account = Ebb.brownie_load_account(str(fname), "alper")
        balance_to_transfer = Ebb._get_balance(account, "wei")
        log(balance_to_transfer)
        log(Ebb._get_balance(collect_account, "wei"))
        if balance_to_transfer > 21000:
            log(Ebb.transfer(balance_to_transfer - 21000, account, collect_account, required_confs=0))
            log(Ebb._get_balance(account))
            log(Ebb._get_balance(collect_account))


def send_eth_to_users(accounts, value):
    for account in accounts:
        _account = account.lower().replace("0x", "")
        fname = Path(expanduser("~/.brownie/accounts")) / _account
        print(fname)
        account = Ebb.brownie_load_account(str(fname), "alper")
        log(Ebb._get_balance(collect_account, "wei"))
        log(Ebb.transfer(value, _collect_account, account, required_confs=0))
        log(Ebb._get_balance(account))
        log(Ebb._get_balance(collect_account))
        # breakpoint()  # DEBUG


def main():
    collect_all_into_base()
    # send_eth_to_users(providers, "0.5 ether")
    # send_eth_to_users(users, "0.2 ether")


if __name__ == "__main__":
    main()
