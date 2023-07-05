#!/usr/bin/env python3

import sys

from broker import cfg
from broker._utils._log import log
from broker._utils.web3_tools import get_tx_status
from broker.errors import QuietExit
from broker.utils import print_tb


def withdraw(address, amount):
    temp = address.balance()
    assert ebb.balanceOf(address) == amount
    tx = ebb.withdraw({"from": address, "gas_price": 0})
    append_gas_cost("withdraw", tx)
    received = address.balance() - temp
    assert to_gwei(amount) == received
    assert ebb.balanceOf(address) == 0
