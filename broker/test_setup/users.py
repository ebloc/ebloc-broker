#!/usr/bin/env python3

import sys
import time
from os.path import expanduser
from pathlib import Path

from broker import cfg
from broker._utils.tools import log
from broker.test_setup.user_set import providers, requesters
from broker.utils import print_tb

# from broker.test_setup.user_set import extra_users

# https://blockexplorer.bloxberg.org/address/0xFD0EbCD42D4c4C2a2281adfDB48177454838C433/transactions
base_account = "0xfd0ebcd42d4c4c2a2281adfdb48177454838c433".lower()
# base_account = "0xd118b6ef83ccf11b34331f1e7285542ddf70bc49".lower()
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
            log(f"==> base_account({base_account})={Ebb._get_balance(base_account)}")


def collect_all_into_base():
    min_balance_amount = Ebb.w3.fromWei(21000, "ether")
    for account in requesters:
        _collect_all_into_base(account, min_balance_amount)

    # for account in providers:
    #     _collect_all_into_base(account, min_balance_amount)

    log(f"==> base_account={Ebb._get_balance(base_account)}")


def transfer_eth(accounts, value, is_force=False):
    for account in accounts:
        _account = account.lower().replace("0x", "")
        fn = Path(expanduser("~/.brownie/accounts")) / _account
        print(fn)
        account = Ebb.brownie_load_account(str(fn), "alper")
        if Ebb._get_balance(account, "gwei") == 0 or is_force:
            try:
                log(Ebb.transfer(value, _base_account, account, required_confs=1))
            except Exception as e:
                log(str(e))
                breakpoint()  # DEBUG

        # log(Ebb._get_balance(account))
        # log(Ebb._get_balance(base_account))
        time.sleep(2)


def main():
    user = "0x72c1a89ff3606aa29686ba8d29e28dccff06430a"
    log(f"==> base_account_balance={Ebb._get_balance(base_account)}\n")
    log(f"==> user_account_balance={Ebb._get_balance(user)}\n")
    owner = Ebb.get_owner()
    log(f"ower_balance ({owner.lower()})=", "bold", end="")
    balances([owner], is_verbose=True)
    balances(providers)
    print("----")
    # balances(requesters)

    # collect_all_into_base()
    # transfer_eth(["0x72c1a89ff3606aa29686ba8d29e28dccff06430a"], "0.5 ether", is_force=True)
    # transfer_eth(["0x29e613b04125c16db3f3613563bfdd0ba24cb629"], "0.3 ether", is_force=True)
    # transfer_eth(["0x4934a70ba8c1c3acfa72e809118bdd9048563a24"], "0.3 ether", is_force=True)
    # transfer_eth(["0xe2e146d6b456760150d78819af7d276a1223a6d4"], "0.3 ether", is_force=True)

    # transfer_eth(providers, "0.01 ether", is_force=True)
    # transfer_eth(requesters, "0.11 ether")
    # transfer_eth(extra_users, "0.1 ether")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print_tb(e)
        sys.exit(1)
