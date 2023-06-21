#!/usr/bin/env python3

import pytest  # noqa: F401

import contract.scripts.lib  # noqa: F401
from broker.cfg import ZERO_ADDRESS
from brownie import accounts
from brownie import *  # noqa


def project():
    print("here")
    accounts[0].deploy(Lib)  # noqa
    ebb = accounts[0].deploy(eBlocBroker)  # noqa
    print(ebb.getOwner())
    try:
        tx = ebb.transferOwnership(ZERO_ADDRESS, {"from": accounts[0]}).raisingFunction()  # noqa
    except:
        tx = history[-1]  # noqa
        print(tx.revert_msg)
