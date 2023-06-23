#!/usr/bin/env python3

import sys
from broker.config import env
from broker import cfg
from broker.test_setup.user_set import requesters, providers
from broker.utils import print_tb


def reset_token_balances(idx, user):
    amount = cfg.Ebb.allowance(env.CONTRACT_ADDRESS, user)
    print(f"[  counter={idx}  ] user={user} amount={amount}")
    if amount > 0:
        cfg.Ebb.transfer_from(env.CONTRACT_ADDRESS, user, amount)


def main():
    for idx, user in enumerate(requesters):
        reset_token_balances(idx, user)

    for idx, user in enumerate(providers):
        reset_token_balances(idx, user)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print_tb(e)
        sys.exit(1)
