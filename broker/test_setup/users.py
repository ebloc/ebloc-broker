#!/usr/bin/env python3

import time
from os.path import expanduser
from pathlib import Path

from broker import cfg
from broker._utils.tools import log
from broker.test_setup.user_set import providers, requesters

# from broker.test_setup.user_set import extra_users

# https://blockexplorer.bloxberg.org/address/0xFD0EbCD42D4c4C2a2281adfDB48177454838C433/transactions
base_account = "0xfd0ebcd42d4c4c2a2281adfdb48177454838c433".lower()
Ebb = cfg.Ebb
_base_account = base_account.replace("0x", "")
fn = str(Path(expanduser("~/.brownie/accounts")) / _base_account)
_base_account = Ebb.brownie_load_account(fn, "alper")


def balances(accounts, is_verbose=False):
    """Print balance of all the users located under ~/.brownie/accounts."""
    for account in accounts:
        _account = account.lower().replace("0x", "")
        fn = Path(expanduser("~/.brownie/accounts")) / _account
        if not is_verbose:
            print(fn)

        account = Ebb.brownie_load_account(str(fn), "alper")
        log(Ebb._get_balance(account), "m")


def _collect_all_into_base(account, min_balance_amount):
    _account = account.lower().replace("0x", "")
    fn = Path(expanduser("~/.brownie/accounts")) / _account
    log(fn)
    account = Ebb.brownie_load_account(str(fn), "alper")
    balance_to_transfer = Ebb._get_balance(account, "ether")
    # log(balance_to_transfer)
    # log(Ebb._get_balance(base_account, "gwei"))
    if balance_to_transfer > min_balance_amount:
        _amount = balance_to_transfer - min_balance_amount
        _required_confs = 1
        tx = Ebb.transfer(f"{_amount} ether", account, base_account, required_confs=_required_confs)
        log(tx)
        if _required_confs > 0:
            log(Ebb._get_balance(account))
            log(f"## base_account={Ebb._get_balance(base_account)}")


def collect_all_into_base():
    min_balance_amount = Ebb.w3.fromWei(21000, "ether")
    for account in requesters:
        _collect_all_into_base(account, min_balance_amount)

    for account in providers:
        _collect_all_into_base(account, min_balance_amount)

    log(f"## base_account={Ebb._get_balance(base_account)}")


def transfer_eth(accounts, value):
    for account in accounts:
        _account = account.lower().replace("0x", "")
        fn = Path(expanduser("~/.brownie/accounts")) / _account
        print(fn)
        account = Ebb.brownie_load_account(str(fn), "alper")
        log(Ebb._get_balance(base_account, "gwei"))
        log(Ebb.transfer(value, _base_account, account, required_confs=0))
        # log(Ebb._get_balance(account))
        # log(Ebb._get_balance(base_account))
        time.sleep(2)


def main():
    log(f"## base_account={Ebb._get_balance(base_account)}\n")
    owner = Ebb.get_owner()
    log(f"ower_balance ({owner.lower()})=", "bold", end="")
    balances([owner], is_verbose=True)
    balances(providers)
    balances(requesters)
    # collect_all_into_base()
    # transfer_eth(["0xd118b6ef83ccf11b34331f1e7285542ddf70bc49"], "0.5 ether")
    # transfer_eth(providers, "0.4 ether")
    # transfer_eth(requesters, "0.1 ether")
    # transfer_eth(extra_users, "0.1 ether")


if __name__ == "__main__":
    main()
