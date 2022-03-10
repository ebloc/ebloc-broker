#!/usr/bin/env python3

import sys

from broker import cfg
from broker._utils._log import log
from broker._utils.web3_tools import get_tx_status
from broker.errors import QuietExit
from broker.utils import print_tb


def _withdraw():
    Ebb = cfg.Ebb
    if len(sys.argv) == 2:
        account = str(sys.argv[1])
    else:
        log("## provide an ethereum account as an argument")
        sys.exit(1)

    try:
        balance = Ebb.get_balance(account)
        if balance > 0:
            log(f"account_balance={balance}", "bold")
            get_tx_status(Ebb.withdraw(account))
        else:
            log("warning: account balance is empty nothing to do")
    except QuietExit:
        pass
    except Exception as e:
        print_tb(e)


if __name__ == "__main__":
    _withdraw()
