#!/usr/bin/env python3

from broker import cfg
from broker._utils.tools import log
from broker.eblocbroker_scripts.utils import Cent
from broker.test_setup.user_set import requesters

# from broker.test_setup.user_set import extra_users

Ebb = cfg.Ebb
owner = Ebb.get_owner()


def _transfer_tokens(accounts, is_verbose=False):
    """Print balance of all the users located under ~/.brownie/accounts."""
    amount_to_send = "2000 usd"
    for account in requesters:
        balance = Ebb.get_balance(account)
        if balance:
            log(f"{account} = {Cent(balance).to('usd')} usd")
        else:
            log(f"{account} = 0")

        if Cent(amount_to_send) != Cent(balance):
            _amount = Cent(amount_to_send).__sub__(balance)
            if _amount > 0:
                Ebb.transfer_tokens(owner, account, _amount)
                # log(f"{account} = {Cent(Ebb.get_balance(account)).to('usd')} usd")

        # _account = account.lower().replace("0x", "")
        # fn = Path(expanduser("~/.brownie/accounts")) / _account
        # if not is_verbose:
        #     print(fn)

        # account = Ebb.brownie_load_account(str(fn), "alper")
        #


def main():
    balance = cfg.Ebb.get_balance(owner)
    log(f"ower_balance ({owner}):", "bold")
    log(f"\t{Cent(balance)} cent ≈ {Cent(balance).to('usd')} usd")

    _transfer_tokens(requesters)

    # balances([owner], is_verbose=True)
    # balances(providers)
    #
    # collect_all_into_base()

    # send_eth_to_users(["0xd118b6ef83ccf11b34331f1e7285542ddf70bc49"], "0.5 ether")
    # send_eth_to_users(providers, "0.4 ether")
    # send_eth_to_users(requesters, "0.1 ether")
    # send_eth_to_users(extra_users, "0.1 ether")


if __name__ == "__main__":
    main()
