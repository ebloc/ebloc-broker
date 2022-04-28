#!/usr/bin/env python3

import time
from os.path import expanduser
from pathlib import Path

from broker import cfg
from broker._utils.tools import log
from broker.test_setup.user_set import providers, requesters

# from broker.test_setup.user_set import extra_users

collect_account = "0xfd0ebcd42d4c4c2a2281adfdb48177454838c433".lower()
Ebb = cfg.Ebb
_collect_account = collect_account.replace("0x", "")
fn = str(Path(expanduser("~/.brownie/accounts")) / _collect_account)
_collect_account = Ebb.brownie_load_account(fn, "alper")
log(f"collect_account={Ebb._get_balance(collect_account)}", "bold")


def balances(accounts, is_silent=False):
    """Print balance of all the users located under ~/.brownie/accounts."""
    for account in accounts:
        _account = account.lower().replace("0x", "")
        fn = Path(expanduser("~/.brownie/accounts")) / _account
        if not is_silent:
            print(fn)

        account = Ebb.brownie_load_account(str(fn), "alper")
        log(Ebb._get_balance(account), "magenta")


def collect_all_into_base():
    for account in requesters:
        _account = account.lower().replace("0x", "")
        fn = Path(expanduser("~/.brownie/accounts")) / _account
        log(fn)
        account = Ebb.brownie_load_account(str(fn), "alper")
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
        fn = Path(expanduser("~/.brownie/accounts")) / _account
        print(fn)
        account = Ebb.brownie_load_account(str(fn), "alper")
        log(Ebb._get_balance(collect_account, "wei"))
        log(Ebb.transfer(value, _collect_account, account, required_confs=0))
        log(Ebb._get_balance(account))
        log(Ebb._get_balance(collect_account))
        time.sleep(1)


def main():
    owner = Ebb.get_owner()
    log(f"ower_balance ({owner})=", "bold", end="")
    balances([owner], is_silent=True)
    balances(providers)
    breakpoint()  # DEBUG
    balances(requesters)
    # collect_all_into_base()
    # send_eth_to_users(["0xd118b6ef83ccf11b34331f1e7285542ddf70bc49"], "0.5 ether")
    # send_eth_to_users(providers, "0.4 ether")
    # send_eth_to_users(requesters, "0.1 ether")
    # send_eth_to_users(extra_users, "0.1 ether")


if __name__ == "__main__":
    main()
