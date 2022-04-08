#!/usr/bin/env python3

from os.path import expanduser
from pathlib import Path

from broker import cfg
from broker._utils.tools import log
from broker.test_setup.user_set import users

# from broker.test_setup.user_set import extra_users

collect_account = "0xfd0ebcd42d4c4c2a2281adfdb48177454838c433".lower()

providers = [
    "0x29e613B04125c16db3f3613563bFdd0BA24Cb629",
    "0x1926b36af775e1312fdebcc46303ecae50d945af",
    "0x4934a70Ba8c1C3aCFA72E809118BDd9048563A24",
    "0x51e2b36469cdbf58863db70cc38652da84d20c67",
]

Ebb = cfg.Ebb
_collect_account = collect_account.replace("0x", "")
fn = str(Path(expanduser("~/.brownie/accounts")) / _collect_account)
_collect_account = Ebb.brownie_load_account(fn, "alper")
log(f"collect_account={Ebb._get_balance(collect_account)}", "bold")


def balances():
    """Prints balance of all the users located under ~/.brownie/accounts."""
    for account in users:
        _account = account.lower().replace("0x", "")
        fn = Path(expanduser("~/.brownie/accounts")) / _account
        print(fn)
        account = Ebb.brownie_load_account(str(fn), "alper")
        log(Ebb._get_balance(account))


def collect_all_into_base():
    for account in users:
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
        # breakpoint()  # DEBUG


def main():
    balances()
    # collect_all_into_base()
    # send_eth_to_users(providers, "0.5 ether")
    # send_eth_to_users(users, "0.2 ether")
    # send_eth_to_users(extra_users, "0.1 ether")


if __name__ == "__main__":
    main()
