#!/usr/bin/env python3

import pytest  # noqa: F401
from tests import test_eblocbroker  # noqa: F401
from utils import ZERO_ADDRESS

import contract.scripts.lib  # noqa: F401
from brownie import *  # noqa


def project():
    accounts[0].deploy(Lib)  # noqa
    ebb = accounts[0].deploy(eBlocBroker)  # noqa

    print(ebb.getOwner())

    try:
        tx = ebb.transferOwnership(ZERO_ADDRESS, {"from": accounts[0]}).raisingFunction()  # noqa
    except:
        tx = history[-1]  # noqa
        print(tx.revert_msg)

    print("END")
